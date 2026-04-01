"""
04_scalable_design.py - スケーラブルな設計パターン

このファイルの目的:
- ワーカーキューパターンの実装を学ぶ
- バッチ処理による効率化を理解する
- サーキットブレーカーパターンを習得する
- フェイルオーバー戦略の実装を学ぶ
- 負荷分散の考え方を理解する

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 04_architecture/04_scalable_design.py

【スケーラブル設計が重要な理由】
単純な実装は小規模では動作しますが、大規模になると問題が起きます:
- 高負荷時にシステムが崩壊する
- 一部の障害が全体に波及する
- パフォーマンスのボトルネックを特定できない

スケーラブル設計パターンによってこれらを解決します。
"""

import os
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from anthropic import Anthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"


def get_client() -> Anthropic:
    """APIクライアントを取得する（Colab・ローカル両対応）"""
    try:
        from google.colab import userdata
        api_key = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')

    return Anthropic(api_key=api_key)


# =============================================================================
# 1. ワーカーキューパターン（Producer-Consumer）
# =============================================================================

@dataclass
class APITask:
    """
    APIリクエストタスク

    キューに積むタスクを表します。
    ワーカースレッドがこのタスクを取り出して実行します。

    Attributes:
        task_id: タスク識別子
        prompt: プロンプト
        max_tokens: 最大トークン数
        result: 実行結果（実行後に設定）
        error: エラー情報（エラー時に設定）
        created_at: タスク作成時刻
        completed_at: タスク完了時刻
    """
    task_id: int
    prompt: str
    max_tokens: int = 256
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    @property
    def wait_time(self) -> Optional[float]:
        """キュー待機時間（秒）"""
        if self.completed_at:
            return self.completed_at - self.created_at
        return None


class WorkerQueue:
    """
    ワーカーキューパターンの実装

    【パターンの説明】
    Producer（生産者）がタスクをキューに追加し、
    Consumer（消費者）がワーカースレッドとしてタスクを処理します。

    このパターンにより:
    - タスクの生産と消費を分離できる
    - 同時リクエスト数を制御できる
    - タスクの優先順位付けが可能
    - 負荷に応じてワーカー数を調整できる

    Attributes:
        num_workers: ワーカースレッド数
        task_queue: タスクキュー
        workers: ワーカースレッドのリスト
        completed_tasks: 完了したタスクのリスト
    """

    def __init__(self, num_workers: int = 3):
        """
        Args:
            num_workers: 同時に実行するワーカー数
        """
        self.num_workers = num_workers
        # queue.Queue はスレッドセーフなキュー
        # maxsize=0 は無制限のキューを意味する
        self.task_queue: queue.Queue = queue.Queue()
        self.workers: list[threading.Thread] = []
        self.completed_tasks: list[APITask] = []
        self._lock = threading.Lock()  # 共有データの排他制御
        self._client = get_client()
        self._running = False

    def start(self) -> None:
        """ワーカースレッドを起動する"""
        self._running = True
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i + 1}",
                daemon=True  # メインスレッド終了時にワーカーも終了
            )
            worker.start()
            self.workers.append(worker)
        print(f"✅ {self.num_workers}個のワーカーを起動しました")

    def stop(self) -> None:
        """ワーカースレッドを停止する"""
        self._running = False
        # 終了シグナル（None）をワーカー数分だけキューに追加
        for _ in self.workers:
            self.task_queue.put(None)

        # 全ワーカーの終了を待機
        for worker in self.workers:
            worker.join(timeout=5.0)
        print("✅ 全ワーカーを停止しました")

    def submit(self, task: APITask) -> None:
        """
        タスクをキューに追加する（Producer側）

        Args:
            task: 実行するタスク
        """
        self.task_queue.put(task)

    def wait_all(self) -> None:
        """キューのすべてのタスクが完了するまで待機する"""
        self.task_queue.join()  # キューが空になるまで待機

    def _worker_loop(self) -> None:
        """
        ワーカースレッドのメインループ（Consumer側）

        キューからタスクを取り出して実行し続ける。
        """
        while self._running:
            try:
                # block=True, timeout=1.0: タスクが来るまで最大1秒待機
                task = self.task_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                continue  # タイムアウトしたらループを継続

            # 終了シグナルを受け取った場合は終了
            if task is None:
                self.task_queue.task_done()
                break

            # タスクを実行
            try:
                response = self._client.messages.create(
                    model=MODEL_NAME,
                    max_tokens=task.max_tokens,
                    messages=[{"role": "user", "content": task.prompt}]
                )
                task.result = response.content[0].text
            except Exception as e:
                task.error = str(e)
            finally:
                task.completed_at = time.time()
                # スレッドセーフに completed_tasks に追加
                with self._lock:
                    self.completed_tasks.append(task)
                # キューにこのタスクの処理が完了したことを通知
                self.task_queue.task_done()


# =============================================================================
# 2. バッチ処理の実装
# =============================================================================

def process_in_batches(
    client: Anthropic,
    prompts: list[str],
    batch_size: int = 5,
    delay_between_batches: float = 1.0,
    max_tokens: int = 200
) -> list[dict]:
    """
    バッチ処理でAPIリクエストを実行する

    大量のリクエストをバッチに分割して処理することで:
    - レート制限を遵守できる
    - メモリ使用量を抑えられる
    - エラーが発生してもバッチ単位で回復できる

    Args:
        client: Anthropicクライアント
        prompts: プロンプトのリスト
        batch_size: 1バッチあたりのリクエスト数
        delay_between_batches: バッチ間の待機時間（秒）
        max_tokens: 最大トークン数

    Returns:
        list[dict]: 各リクエストの結果
    """
    results = []
    total = len(prompts)

    # リストをバッチサイズで分割
    # range(0, total, batch_size) で batch_size 個ずつ処理
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = prompts[batch_start:batch_end]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"  バッチ {batch_num}/{total_batches} を処理中 "
              f"（{batch_start + 1}〜{batch_end}/{total}件）...")

        for i, prompt in enumerate(batch):
            try:
                response = client.messages.create(
                    model=MODEL_NAME,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                results.append({
                    "index": batch_start + i,
                    "prompt": prompt[:40],
                    "text": response.content[0].text[:60],
                    "success": True
                })
            except Exception as e:
                results.append({
                    "index": batch_start + i,
                    "prompt": prompt[:40],
                    "text": None,
                    "success": False,
                    "error": str(e)
                })

        # バッチ間で待機（最後のバッチでは不要）
        if batch_end < total:
            time.sleep(delay_between_batches)

    return results


# =============================================================================
# 3. サーキットブレーカーパターン
# =============================================================================

class CircuitState(Enum):
    """
    サーキットブレーカーの状態

    【状態遷移の説明】
    CLOSED（通常）
      ↓ エラーが閾値を超えた場合
    OPEN（遮断）
      ↓ 一定時間経過後
    HALF_OPEN（試行）
      ↓ 成功した場合  ↓ 失敗した場合
    CLOSED           OPEN

    この状態遷移により、障害が発生したサービスへの
    連続リクエストを防ぎ、回復を待つ。
    """
    CLOSED = "CLOSED"      # 通常状態（リクエストを通す）
    OPEN = "OPEN"          # 遮断状態（リクエストをブロック）
    HALF_OPEN = "HALF_OPEN"  # 試行状態（1リクエストだけ通す）


class CircuitBreaker:
    """
    サーキットブレーカーパターンの実装

    連続してエラーが発生した場合にAPIコールを一時停止し、
    サービス全体の障害を防ぐパターン。

    例え: 電気回路のブレーカー（過負荷時に自動遮断）

    Attributes:
        failure_threshold: OPEN になるまでの連続エラー数
        recovery_timeout: OPEN → HALF_OPEN に移行するまでの時間（秒）
        state: 現在の状態
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0
    ):
        """
        Args:
            failure_threshold: 連続エラー数の閾値（これを超えるとOPEN）
            recovery_timeout: OPEN 状態の維持時間（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._success_count = 0  # HALF_OPEN 時の成功カウント

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        サーキットブレーカーを通してAPIを呼び出す

        Args:
            func: 呼び出す関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数

        Returns:
            Any: 関数の戻り値

        Raises:
            RuntimeError: OPEN 状態でリクエストをブロックした場合
        """
        # OPEN 状態の場合: リクエストをブロック
        if self.state == CircuitState.OPEN:
            # タイムアウトが経過したら HALF_OPEN に移行
            if (self._last_failure_time
                    and time.time() - self._last_failure_time > self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self._success_count = 0
                print(f"  🔄 サーキットブレーカー: OPEN → HALF_OPEN（{self.recovery_timeout}秒経過）")
            else:
                remaining = (self._last_failure_time or 0) + self.recovery_timeout - time.time()
                raise RuntimeError(
                    f"サーキットブレーカーOPEN: リクエストをブロックしています。"
                    f"残り{remaining:.1f}秒後に回復試行します。"
                )

        # 関数を実行
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """成功時の処理"""
        if self.state == CircuitState.HALF_OPEN:
            self._success_count += 1
            # HALF_OPEN で1回成功したら CLOSED に移行
            self.state = CircuitState.CLOSED
            self._failure_count = 0
            print("  ✅ サーキットブレーカー: HALF_OPEN → CLOSED（回復成功）")
        else:
            # CLOSED 状態では失敗カウントをリセット
            self._failure_count = 0

    def _on_failure(self) -> None:
        """失敗時の処理"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # HALF_OPEN で失敗したら再び OPEN に移行
            self.state = CircuitState.OPEN
            print("  ❌ サーキットブレーカー: HALF_OPEN → OPEN（回復失敗）")

        elif (self.state == CircuitState.CLOSED
              and self._failure_count >= self.failure_threshold):
            # CLOSED で閾値を超えたら OPEN に移行
            self.state = CircuitState.OPEN
            print(f"  ⚡ サーキットブレーカー: CLOSED → OPEN "
                  f"（連続エラー {self._failure_count}回）")

    @property
    def status(self) -> dict:
        """サーキットブレーカーの現在状態を返す"""
        return {
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
        }


# =============================================================================
# 4. フェイルオーバー戦略
# =============================================================================

class FailoverAPIClient:
    """
    フェイルオーバー機能を持つAPIクライアント

    プライマリクライアントが失敗した場合、
    バックアップの処理（フォールバック関数）に切り替えます。

    Attributes:
        primary_client: プライマリのAPIクライアント
        circuit_breaker: サーキットブレーカー
        fallback_func: フォールバック関数
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        fallback_func: Optional[Callable[[str], str]] = None
    ):
        """
        Args:
            failure_threshold: サーキットブレーカーの閾値
            recovery_timeout: OPEN 状態の維持時間（秒）
            fallback_func: フォールバック関数（Noneの場合はデフォルトメッセージ）
        """
        self.primary_client = get_client()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
        # フォールバック関数: プライマリが使えない場合の代替処理
        self.fallback_func = fallback_func or self._default_fallback

    @staticmethod
    def _default_fallback(prompt: str) -> str:
        """デフォルトのフォールバック処理（シンプルなルールベース応答）"""
        if "Python" in prompt:
            return "Pythonに関するご質問は、現在サービスが制限中のため後ほどお試しください。"
        return "申し訳ございませんが、現在サービスが一時的に利用できません。しばらくしてからお試しください。"

    def query(self, prompt: str, max_tokens: int = 256) -> dict:
        """
        フェイルオーバー付きAPIクエリ

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            dict: {
                "text": レスポンス,
                "source": "primary" または "fallback",
                "success": 成功フラグ
            }
        """
        def _api_call() -> str:
            response = self.primary_client.messages.create(
                model=MODEL_NAME,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        try:
            text = self.circuit_breaker.call(_api_call)
            return {"text": text, "source": "primary", "success": True}

        except RuntimeError as e:
            # サーキットブレーカーがOPEN: フォールバックを使用
            fallback_text = self.fallback_func(prompt)
            return {
                "text": fallback_text,
                "source": "fallback",
                "success": False,
                "reason": str(e)
            }

        except Exception as e:
            # その他のエラー: フォールバックを使用
            fallback_text = self.fallback_func(prompt)
            return {
                "text": fallback_text,
                "source": "fallback",
                "success": False,
                "reason": str(e)
            }


# =============================================================================
# 5. デモ関数
# =============================================================================

def demonstrate_worker_queue() -> None:
    """ワーカーキューパターンのデモ"""
    print("\n--- 1. ワーカーキューパターンのデモ ---")

    prompts = [
        "Pythonとは？1文で。",
        "Javaとは？1文で。",
        "JavaScriptとは？1文で。",
        "Goとは？1文で。",
        "Rustとは？1文で。",
    ]

    # ワーカーキューを作成（3ワーカー）
    wq = WorkerQueue(num_workers=3)
    wq.start()

    # タスクをキューに投入
    tasks = []
    for i, prompt in enumerate(prompts):
        task = APITask(task_id=i + 1, prompt=prompt, max_tokens=50)
        wq.submit(task)
        tasks.append(task)
        print(f"  [タスク{i + 1}] キューに追加: {prompt[:30]}")

    # 全タスクの完了を待機
    print("\n  全タスクの完了を待機中...")
    start = time.time()
    wq.wait_all()
    elapsed = time.time() - start
    wq.stop()

    print(f"\n  完了（{elapsed:.3f}秒）:")
    for task in sorted(wq.completed_tasks, key=lambda t: t.task_id):
        status = "✅" if task.result else "❌"
        print(f"  {status} [タスク{task.task_id}] {task.prompt[:25]}... "
              f"→ {(task.result or task.error or '')[:40]}...")


def demonstrate_batch_processing(client: Anthropic) -> None:
    """バッチ処理のデモ"""
    print("\n--- 2. バッチ処理のデモ ---")

    prompts = [
        f"プログラミング言語を1つ挙げてください（{i}番目）。"
        for i in range(1, 9)  # 8個のプロンプト
    ]

    print(f"合計 {len(prompts)} 件を バッチサイズ3 で処理します")
    start = time.time()
    results = process_in_batches(
        client,
        prompts,
        batch_size=3,
        delay_between_batches=0.5,
        max_tokens=30
    )
    elapsed = time.time() - start

    success_count = sum(1 for r in results if r["success"])
    print(f"\n  完了（{elapsed:.3f}秒）: {success_count}/{len(results)} 件成功")


def demonstrate_circuit_breaker() -> None:
    """サーキットブレーカーのデモ（APIなし）"""
    print("\n--- 3. サーキットブレーカーのデモ ---")
    print("【状態遷移のシミュレーション】")

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)

    def simulate_success() -> str:
        return "成功"

    def simulate_failure() -> str:
        raise Exception("模擬エラー")

    # CLOSED 状態から開始
    print(f"\n初期状態: {cb.status['state']}")

    # 2回失敗（まだ CLOSED）
    for i in range(2):
        try:
            cb.call(simulate_failure)
        except Exception:
            print(f"  失敗 {i + 1}回目 → 状態: {cb.state.value} "
                  f"（カウント: {cb._failure_count}/{cb.failure_threshold}）")

    # 3回目で OPEN に移行
    try:
        cb.call(simulate_failure)
    except Exception:
        print(f"  失敗 3回目 → 状態: {cb.state.value} ← OPEN に移行！")

    # OPEN 状態でリクエストをブロック
    try:
        cb.call(simulate_success)
    except RuntimeError as e:
        print(f"  ブロック: {str(e)[:60]}...")

    print("\n  （5秒後に HALF_OPEN に移行するシミュレーション）")
    # 実際には time.sleep(5) するが、デモのためにスキップ
    # テスト用に内部状態を直接変更
    cb._last_failure_time = time.time() - 6.0  # 6秒前に設定

    # HALF_OPEN: 試行リクエスト成功 → CLOSED に戻る
    try:
        cb.call(simulate_success)
        print(f"  成功 → 状態: {cb.state.value} ← CLOSED に戻った！")
    except Exception:
        pass


def scalable_design_best_practices() -> None:
    """スケーラブル設計のベストプラクティスを表示する"""
    print("\n--- スケーラブル設計のベストプラクティス ---")

    best_practices = """
【✅ スケーラブル設計のポイント】

1. ワーカーキューパターン（Producer-Consumer）
   - タスクの生産と消費を分離する
   - queue.Queue でスレッドセーフなキューを実装
   - num_workers でスループットとレート制限のバランスを調整

2. バッチ処理
   - 大量のリクエストをバッチに分割してレート制限を守る
   - バッチ間に待機時間を設けて負荷を分散する
   - エラーが発生してもバッチ単位で回復できる

3. サーキットブレーカーパターン
   - 状態: CLOSED（正常）→ OPEN（遮断）→ HALF_OPEN（試行）
   - OPEN 中はリクエストをブロックして障害の拡大を防ぐ
   - HALF_OPEN で回復を確認してから CLOSED に戻る
   - failure_threshold と recovery_timeout を適切に設定する

4. フェイルオーバー戦略
   - プライマリが失敗した場合のフォールバックを必ず用意する
   - キャッシュされたレスポンスを返す
   - ルールベースの簡易応答を返す
   - ユーザーに適切なエラーメッセージを表示する

5. 接続プールの使用
   - Anthropic SDK は内部で接続プールを管理する
   - 同じクライアントインスタンスを再利用する（都度生成しない）
   - max_connections パラメータで接続数を制御できる

【💡 CCA試験のポイント】
- ワーカーキュー = Producer-Consumer パターン
- サーキットブレーカーの3状態: CLOSED / OPEN / HALF_OPEN
- バッチ処理 = レート制限遵守 + 効率化
- フェイルオーバー = 障害時の代替処理
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 60)
    print("スケーラブルな設計パターン")
    print("=" * 60)

    # 3. サーキットブレーカーのデモ（APIなし）
    demonstrate_circuit_breaker()

    # ベストプラクティス表示（APIなし）
    scalable_design_best_practices()

    # API を使ったデモ
    print("\n--- API接続テスト ---")
    api_client = get_client()

    # 1. ワーカーキューのデモ
    demonstrate_worker_queue()

    # 2. バッチ処理のデモ
    demonstrate_batch_processing(api_client)

    print("\n✅ 完了！次はexercises/exercise_01.pyに進んでください。")
