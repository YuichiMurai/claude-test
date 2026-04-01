"""
exercise_03.py - 練習問題3: スケーラブルアーキテクチャの構築

難易度: ⭐⭐⭐⭐ 上級

目的:
大規模システムを想定したアーキテクチャを設計・実装する。

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行

【実装する機能】
1. ワーカーキューパターン
2. バッチ処理
3. サーキットブレーカー
4. フェイルオーバー
5. 負荷分散（ラウンドロビン）

【参考ファイル】
- 04_architecture/04_scalable_design.py - スケーラブル設計実装
"""

import itertools  # noqa: F401 - students will use itertools.cycle() in TODO 3-1 (LoadBalancer._iterator)
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterator, Optional

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
# TODO 1: ワーカーキューパターンを実装する
# =============================================================================

@dataclass
class Task:
    """
    処理タスク

    Attributes:
        task_id: タスク識別子
        prompt: プロンプト
        max_tokens: 最大トークン数
        result: 実行結果（実行後に設定）
        error: エラー情報（エラー時に設定）
        created_at: 作成時刻
        completed_at: 完了時刻
    """
    task_id: int
    prompt: str
    max_tokens: int = 100
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class ScalableWorkerQueue:
    """
    スケーラブルなワーカーキュー

    【ヒント】
    - queue.Queue() でスレッドセーフなキューを作成する
    - threading.Thread() でワーカースレッドを作成する
    - threading.Lock() で共有データの排他制御を行う
    - ワーカーループでは task_queue.task_done() を必ず呼ぶ
    """

    def __init__(self, num_workers: int = 3):
        """
        Args:
            num_workers: ワーカー数
        """
        self.num_workers = num_workers
        self.task_queue: queue.Queue = queue.Queue()
        self.completed_tasks: list[Task] = []
        self._lock = threading.Lock()
        self._client = get_client()
        self._workers: list[threading.Thread] = []
        self._running = False

    def start(self) -> None:
        """
        TODO 1-1: ワーカースレッドを起動する

        手順:
        1. self._running = True に設定
        2. num_workers 個のワーカースレッドを作成・起動
           - target=self._worker_loop
           - name=f"Worker-{i+1}"
           - daemon=True（メインスレッド終了時に自動終了）
        3. self._workers にスレッドを追加
        4. 起動メッセージを print() で表示
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def stop(self) -> None:
        """
        TODO 1-2: ワーカースレッドを停止する

        手順:
        1. self._running = False に設定
        2. ワーカー数分の None をキューに追加（終了シグナル）
        3. 各ワーカーの join(timeout=5.0) を待機
        4. 停止メッセージを print() で表示
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def submit(self, task: Task) -> None:
        """タスクをキューに追加する"""
        self.task_queue.put(task)

    def wait_all(self) -> None:
        """全タスクの完了を待機する"""
        self.task_queue.join()

    def _worker_loop(self) -> None:
        """
        TODO 1-3: ワーカーのメインループを実装する

        手順:
        1. self._running が True の間ループ
        2. task_queue.get(block=True, timeout=1.0) でタスクを取得
           - queue.Empty 例外が発生したら continue（タイムアウト）
        3. task が None の場合: task_done() を呼んで break
        4. タスクを実行（self._client.messages.create(...)）:
           - 成功: task.result = response.content[0].text
           - 失敗: task.error = str(e)
        5. task.completed_at = time.time() を設定
        6. self._lock を使って self.completed_tasks にタスクを追加
        7. task_queue.task_done() を呼ぶ
        """
        # TODO: ここを実装してください
        pass  # 削除してください


# =============================================================================
# TODO 2: サーキットブレーカーを実装する
# =============================================================================

class BreakerState(Enum):
    """サーキットブレーカーの状態"""
    CLOSED = "CLOSED"        # 通常状態
    OPEN = "OPEN"            # 遮断状態
    HALF_OPEN = "HALF_OPEN"  # 試行状態


class ScalableCircuitBreaker:
    """
    サーキットブレーカーパターン

    【状態遷移】
    CLOSED → (連続エラーが閾値を超える) → OPEN
    OPEN → (recovery_timeout 秒経過) → HALF_OPEN
    HALF_OPEN → (成功) → CLOSED
    HALF_OPEN → (失敗) → OPEN

    【ヒント】
    - _failure_count で連続エラー数を管理する
    - _last_failure_time でOPEN になった時刻を記録する
    - OPEN 状態でリクエストを受けたら RuntimeError を発生させる
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        """
        Args:
            failure_threshold: OPEN になるまでの連続エラー数
            recovery_timeout: OPEN 状態の維持時間（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = BreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        TODO 2: サーキットブレーカーを通して関数を呼び出す

        手順:
        1. OPEN 状態の場合:
           a. recovery_timeout を超えていれば HALF_OPEN に移行してログ表示
           b. それ以外は RuntimeError を発生させる
        2. func(*args, **kwargs) を実行する
        3. 成功時: _on_success() を呼ぶ
        4. 失敗時: _on_failure() を呼んで例外を再 raise する

        Args:
            func: 呼び出す関数
            *args: 関数の引数
            **kwargs: キーワード引数

        Returns:
            Any: 関数の戻り値

        Raises:
            RuntimeError: OPEN 状態でリクエストがブロックされた場合
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def _on_success(self) -> None:
        """
        TODO 2-1: 成功時の状態更新

        - HALF_OPEN の場合: CLOSED に移行して _failure_count をリセット
        - CLOSED の場合: _failure_count をリセット
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def _on_failure(self) -> None:
        """
        TODO 2-2: 失敗時の状態更新

        - _failure_count を増やす
        - _last_failure_time を現在時刻に更新
        - HALF_OPEN の場合: OPEN に移行してログ表示
        - CLOSED で _failure_count >= failure_threshold の場合: OPEN に移行してログ表示
        """
        # TODO: ここを実装してください
        pass  # 削除してください


# =============================================================================
# TODO 3: 負荷分散（ラウンドロビン）を実装する
# =============================================================================

class LoadBalancer:
    """
    ラウンドロビンによる負荷分散

    複数のAPIクライアントに均等にリクエストを分散する。

    【ヒント】
    - itertools.cycle() でラウンドロビンのイテレータを作成する
    - next(self._iterator) で次のクライアントを取得する
    """

    def __init__(self, num_clients: int = 3):
        """
        Args:
            num_clients: クライアント数（並列接続数）
        """
        # 複数のクライアントインスタンスを作成
        self.clients = [get_client() for _ in range(num_clients)]
        # itertools.cycle() でループするイテレータを作成
        # TODO 3-1: self._iterator を itertools.cycle(self.clients) で初期化する
        self._iterator: Iterator[Anthropic] = iter([])  # TODO: ここを修正してください
        self._lock = threading.Lock()
        self._request_counts = [0] * num_clients  # 各クライアントへのリクエスト数

    def get_client(self) -> Anthropic:
        """
        TODO 3-2: 次のクライアントをラウンドロビンで取得する

        スレッドセーフに self._lock を使って次のクライアントを返す。
        また、対応する _request_counts を増やす。

        Returns:
            Anthropic: 次のクライアント
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def query(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """
        負荷分散してAPIリクエストを実行する

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            Optional[str]: レスポンステキスト
        """
        client = self.get_client()
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return None

    @property
    def distribution_stats(self) -> dict:
        """負荷分散の統計を返す"""
        total = sum(self._request_counts)
        return {
            "total_requests": total,
            "per_client": self._request_counts,
            "distribution": [
                f"{c}/{total}" for c in self._request_counts
            ] if total > 0 else []
        }


# =============================================================================
# TODO 4: フェイルオーバー機能を持つクライアントを実装する
# =============================================================================

class ScalableAPISystem:
    """
    ワーカーキュー + サーキットブレーカー + フェイルオーバーを統合したシステム
    """

    def __init__(
        self,
        num_workers: int = 3,
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout: float = 30.0,
        fallback_func: Optional[Callable[[str], str]] = None
    ):
        self.worker_queue = ScalableWorkerQueue(num_workers=num_workers)
        self.circuit_breaker = ScalableCircuitBreaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout=circuit_recovery_timeout
        )
        self._primary_client = get_client()
        self.fallback_func = fallback_func or self._default_fallback

    @staticmethod
    def _default_fallback(prompt: str) -> str:
        """デフォルトフォールバック応答"""
        return "現在サービスが一時的に利用できません。しばらくしてからお試しください。"

    def query_with_failover(self, prompt: str, max_tokens: int = 100) -> dict:
        """
        TODO 4: サーキットブレーカー + フェイルオーバー付きクエリ

        手順:
        1. def _api_call() を定義: self._primary_client で API を呼び出す
        2. self.circuit_breaker.call(_api_call) を実行する
        3. RuntimeError が発生した場合（OPEN 状態）: フォールバックを返す
           {"text": fallback_func(prompt), "source": "fallback", "success": False}
        4. その他の例外: フォールバックを返す
        5. 成功: {"text": text, "source": "primary", "success": True}

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            dict: {"text": ..., "source": "primary"/"fallback", "success": bool}
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def process_tasks_via_queue(self, prompts: list[str]) -> list[Task]:
        """
        ワーカーキューでタスクを処理する

        Args:
            prompts: プロンプトのリスト

        Returns:
            list[Task]: 完了したタスクのリスト
        """
        self.worker_queue.start()

        tasks = []
        for i, prompt in enumerate(prompts):
            task = Task(task_id=i + 1, prompt=prompt, max_tokens=50)
            self.worker_queue.submit(task)
            tasks.append(task)

        self.worker_queue.wait_all()
        self.worker_queue.stop()

        return self.worker_queue.completed_tasks


# =============================================================================
# デモ関数
# =============================================================================

def demonstrate_circuit_breaker_simulation() -> None:
    """サーキットブレーカーのシミュレーション（APIなし）"""
    print("\n--- サーキットブレーカーのシミュレーション ---")
    cb = ScalableCircuitBreaker(failure_threshold=3, recovery_timeout=5.0)

    def succeed() -> str:
        return "成功"

    def fail() -> str:
        raise Exception("模擬エラー")

    print(f"初期状態: {cb.state.value}")

    for i in range(3):
        try:
            cb.call(fail)
        except Exception:
            print(f"  失敗{i + 1}回目 → 状態: {cb.state.value}")

    try:
        cb.call(succeed)
    except RuntimeError as e:
        print(f"  ブロック: {str(e)[:60]}...")

    # 内部タイマーを操作して回復をシミュレート
    cb._last_failure_time = time.time() - 6.0
    try:
        cb.call(succeed)
        print(f"  回復成功 → 状態: {cb.state.value}")
    except Exception:
        pass


def main() -> None:
    """スケーラブルアーキテクチャのデモ"""
    print("=" * 60)
    print("練習問題3: スケーラブルアーキテクチャ")
    print("=" * 60)

    # 1. サーキットブレーカーのシミュレーション（APIなし）
    demonstrate_circuit_breaker_simulation()

    # 2. ワーカーキューのデモ
    print("\n--- ワーカーキューパターンのデモ ---")
    system = ScalableAPISystem(num_workers=3)

    prompts = [
        "Pythonとは？1文で。",
        "Javaとは？1文で。",
        "JavaScriptとは？1文で。",
        "Goとは？1文で。",
        "Rustとは？1文で。",
    ]

    print(f"\n{len(prompts)}件のタスクを処理します...")
    start = time.time()
    completed = system.process_tasks_via_queue(prompts)
    elapsed = time.time() - start

    success_count = sum(1 for t in completed if t.result)
    print(f"\n完了（{elapsed:.3f}秒）: {success_count}/{len(prompts)}件成功")
    for task in sorted(completed, key=lambda t: t.task_id):
        status = "✅" if task.result else "❌"
        text = (task.result or task.error or "")[:40]
        print(f"  {status} [タスク{task.task_id}] {task.prompt[:20]}... → {text}...")

    # 3. 負荷分散のデモ
    print("\n--- 負荷分散のデモ ---")
    lb = LoadBalancer(num_clients=3)
    for i, prompt in enumerate(prompts[:3]):
        result = lb.query(prompt, max_tokens=30)
        print(f"  [クライアント{(i % 3) + 1}] {prompt[:20]}... → {(result or '')[:40]}...")

    stats = lb.distribution_stats
    print(f"\n負荷分散統計: {stats.get('distribution', [])}")

    # 4. フェイルオーバーのデモ
    print("\n--- フェイルオーバーのデモ ---")
    failover_client = ScalableAPISystem(
        circuit_failure_threshold=3,
        circuit_recovery_timeout=60.0
    )

    result = failover_client.query_with_failover(
        "TypeScriptとは？1文で。", max_tokens=50
    )
    if result:
        source = result.get("source", "unknown")
        text = result.get("text", "")
        print(f"  ソース: {source} → {(text or '')[:50]}...")
    else:
        print("  レスポンスなし（実装を確認してください）")

    print("\n✅ 完了！Phase 4の全練習問題が終了しました。お疲れ様でした！")


if __name__ == "__main__":
    main()
