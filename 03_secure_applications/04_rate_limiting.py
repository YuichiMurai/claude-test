"""
04_rate_limiting.py - レート制限の実装

このファイルの目的:
- トークンバケットアルゴリズムによるレート制限を実装する
- リクエストキューイングの仕組みを理解する
- 429エラー（レート制限）の適切な処理方法を学ぶ
- スレッドセーフなレート制限の実装を習得する
- レート制限の監視と可視化を学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 03_secure_applications/04_rate_limiting.py

【Anthropic APIのレート制限について】
Anthropic API には以下の制限があります（プランにより異なる）:
- RPM (Requests Per Minute): 1分あたりのリクエスト数
- TPM (Tokens Per Minute): 1分あたりのトークン数
- ITPM (Input Tokens Per Minute): 1分あたりの入力トークン数

レート制限を超えると 429 Too Many Requests エラーが返されます。
事前のレート制限実装により、このエラーを事前に防げます。
"""

import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import anthropic
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


@dataclass
class RateLimitStats:
    """レート制限の統計情報"""
    total_requests: int = 0       # 総リクエスト数
    successful_requests: int = 0  # 成功したリクエスト数
    throttled_requests: int = 0   # スロットルされたリクエスト数
    total_wait_time: float = 0.0  # 合計待機時間（秒）
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed_time(self) -> float:
        """経過時間（秒）"""
        return time.time() - self.start_time

    @property
    def requests_per_minute(self) -> float:
        """実際のリクエスト/分"""
        elapsed = self.elapsed_time
        if elapsed <= 0:
            return 0.0
        return (self.total_requests / elapsed) * 60

    def summary(self) -> str:
        """統計サマリーを返す"""
        return (
            f"統計情報:\n"
            f"  総リクエスト数: {self.total_requests}\n"
            f"  成功: {self.successful_requests}\n"
            f"  スロットル: {self.throttled_requests}\n"
            f"  合計待機時間: {self.total_wait_time:.2f}秒\n"
            f"  経過時間: {self.elapsed_time:.2f}秒\n"
            f"  実際のRPM: {self.requests_per_minute:.1f}"
        )


class TokenBucketRateLimiter:
    """
    トークンバケットアルゴリズムによるレート制限クラス

    【トークンバケットアルゴリズムとは？】
    バケット（容器）にトークン（許可証）が一定レートで補充され、
    リクエストを送るたびにトークンを消費するアルゴリズムです。

    - バースト（一時的な急増）を許可しつつ、平均レートを制限できる
    - シンプルで効率的な実装が可能
    - スレッドセーフな実装が重要

    例: capacity=10, refill_rate=5/秒
    → バケットに最大10トークン
    → 毎秒5トークン補充
    → 空になったら補充を待つ必要がある
    """

    def __init__(
        self,
        capacity: float,     # バケットの最大容量（最大バーストサイズ）
        refill_rate: float,  # 1秒あたりのトークン補充量（レート制限値）
        name: str = "default"
    ) -> None:
        """
        レートリミッターを初期化する

        Args:
            capacity: バケットの最大容量
            refill_rate: 1秒あたりのトークン補充量
            name: リミッターの名前（ログ用）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.name = name

        # 現在のトークン数（最初は満タン）
        self.tokens = capacity

        # 最後にトークンを補充した時刻
        self.last_refill_time = time.time()

        # スレッドセーフのためのロック
        # 複数スレッドから同時にアクセスされても正確に動作する
        self._lock = threading.Lock()

        # 統計情報
        self.stats = RateLimitStats()

    def _refill(self) -> None:
        """
        経過時間に応じてトークンを補充する（内部メソッド）

        このメソッドはロックを取得した状態で呼び出す必要があります。
        """
        now = time.time()
        elapsed = now - self.last_refill_time

        # 経過時間に応じてトークンを補充
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = now

    def acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """
        指定された数のトークンを取得する（ブロッキング）

        トークンが不足している場合は、補充されるまで待機します。

        Args:
            tokens: 必要なトークン数
            timeout: 最大待機時間（秒）、Noneの場合は無制限

        Returns:
            bool: トークン取得に成功したかどうか
        """
        start_time = time.time()
        self.stats.total_requests += 1

        while True:
            with self._lock:
                # トークンを補充
                self._refill()

                if self.tokens >= tokens:
                    # トークンが十分にある場合は消費して成功
                    self.tokens -= tokens
                    self.stats.successful_requests += 1
                    return True

                # 必要なトークンが補充されるまでの待機時間を計算
                deficit = tokens - self.tokens
                wait_time = deficit / self.refill_rate

            # タイムアウトチェック
            elapsed = time.time() - start_time
            if timeout is not None and elapsed + wait_time > timeout:
                self.stats.throttled_requests += 1
                return False

            # 待機（ロックを解放した状態で）
            actual_wait = min(wait_time, 0.1)  # 最大0.1秒ごとにチェック
            time.sleep(actual_wait)
            self.stats.total_wait_time += actual_wait

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """
        トークンの取得を試みる（ノンブロッキング）

        トークンが不足している場合は即座にFalseを返します。

        Args:
            tokens: 必要なトークン数

        Returns:
            bool: トークン取得に成功したかどうか
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                self.stats.total_requests += 1
                self.stats.successful_requests += 1
                return True
            self.stats.total_requests += 1
            self.stats.throttled_requests += 1
            return False

    @property
    def current_tokens(self) -> float:
        """現在のトークン数"""
        with self._lock:
            self._refill()
            return self.tokens

    def status(self) -> str:
        """現在のステータスを返す"""
        return (
            f"[{self.name}] トークン: {self.current_tokens:.1f}/{self.capacity} "
            f"(補充レート: {self.refill_rate}/秒)"
        )


class SlidingWindowRateLimiter:
    """
    スライディングウィンドウによるレート制限クラス

    【スライディングウィンドウとは？】
    直近N秒間のリクエスト数を追跡して、制限を超えないようにします。
    トークンバケットより正確な制限が可能ですが、メモリ使用量が多くなります。

    例: max_requests=60, window_seconds=60
    → 常に直近60秒間で最大60リクエストに制限
    """

    def __init__(
        self,
        max_requests: int,      # ウィンドウ内の最大リクエスト数
        window_seconds: float,  # ウィンドウのサイズ（秒）
        name: str = "sliding_window"
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name

        # リクエストのタイムスタンプを記録するキュー
        self._requests: deque[float] = deque()
        self._lock = threading.Lock()
        self.stats = RateLimitStats()

    def _cleanup_old_requests(self) -> None:
        """ウィンドウ外の古いリクエストを削除する（内部メソッド）"""
        now = time.time()
        cutoff = now - self.window_seconds
        while self._requests and self._requests[0] <= cutoff:
            self._requests.popleft()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        リクエストの実行許可を取得する

        Args:
            timeout: 最大待機時間（秒）

        Returns:
            bool: 許可が取得できたかどうか
        """
        start_time = time.time()
        self.stats.total_requests += 1

        while True:
            with self._lock:
                self._cleanup_old_requests()

                if len(self._requests) < self.max_requests:
                    # ウィンドウ内のリクエスト数が制限未満
                    self._requests.append(time.time())
                    self.stats.successful_requests += 1
                    return True

                # 最古のリクエストが期限切れになるまでの待機時間
                oldest = self._requests[0]
                wait_time = oldest + self.window_seconds - time.time()

            # タイムアウトチェック
            elapsed = time.time() - start_time
            if timeout is not None and elapsed + wait_time > timeout:
                self.stats.throttled_requests += 1
                return False

            if wait_time > 0:
                actual_wait = min(wait_time, 0.1)
                time.sleep(actual_wait)
                self.stats.total_wait_time += actual_wait

    @property
    def current_count(self) -> int:
        """現在のウィンドウ内のリクエスト数"""
        with self._lock:
            self._cleanup_old_requests()
            return len(self._requests)

    def status(self) -> str:
        """現在のステータスを返す"""
        return (
            f"[{self.name}] リクエスト: {self.current_count}/{self.max_requests} "
            f"（直近{self.window_seconds}秒間）"
        )


class RateLimitedAPIClient:
    """
    レート制限機能を内蔵したAPIクライアントクラス

    トークンバケットとスライディングウィンドウを組み合わせて、
    より堅牢なレート制限を実現します。
    """

    def __init__(
        self,
        client: Anthropic,
        rpm_limit: int = 50,      # 1分あたりの最大リクエスト数
        tpm_limit: int = 50000,   # 1分あたりの最大トークン数
    ) -> None:
        """
        レート制限付きAPIクライアントを初期化する

        Args:
            client: Anthropicクライアント
            rpm_limit: 1分あたりの最大リクエスト数
            tpm_limit: 1分あたりの最大トークン数（概算）
        """
        self.client = client

        # リクエスト数制限（スライディングウィンドウ）
        self.request_limiter = SlidingWindowRateLimiter(
            max_requests=rpm_limit,
            window_seconds=60.0,
            name="RPM Limiter"
        )

        # トークン消費制限（トークンバケット）
        # tpm_limitを1秒あたりのレートに変換
        tokens_per_second = tpm_limit / 60.0
        self.token_limiter = TokenBucketRateLimiter(
            capacity=tpm_limit,        # 最大バースト=1分分のトークン
            refill_rate=tokens_per_second,
            name="TPM Limiter"
        )

    def create_message(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 512,
        estimated_tokens: int = 100  # 入力トークン数の推定値
    ) -> Optional[str]:
        """
        レート制限を考慮してメッセージを作成する

        Args:
            messages: メッセージリスト
            system: システムプロンプト
            max_tokens: 最大出力トークン数
            estimated_tokens: 入力トークン数の推定値

        Returns:
            Optional[str]: レスポンステキスト
        """
        # 推定総トークン数（入力 + 最大出力）
        total_estimated_tokens = estimated_tokens + max_tokens

        # リクエスト数制限のチェック（最大5秒待機）
        print(f"  {self.request_limiter.status()}")
        if not self.request_limiter.acquire(timeout=5.0):
            print("  ⚠️  リクエスト制限に達しました")
            return None

        # トークン数制限のチェック（最大5秒待機）
        print(f"  {self.token_limiter.status()}")
        if not self.token_limiter.acquire(tokens=float(total_estimated_tokens), timeout=5.0):
            print("  ⚠️  トークン制限に達しました")
            return None

        # APIコール
        try:
            request_params: dict = {
                "model": MODEL_NAME,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system:
                request_params["system"] = system

            response = self.client.messages.create(**request_params)
            return response.content[0].text

        except anthropic.RateLimitError as e:
            # それでも429が返ってきた場合（推定が不正確だった場合）
            print(f"  ❌ 429 レート制限エラー（推定が不十分でした）: {e}")
            return None
        except Exception as e:
            print(f"  ❌ APIエラー: {e}")
            return None

    def status(self) -> str:
        """現在のレート制限状況を返す"""
        return (
            f"レート制限状況:\n"
            f"  {self.request_limiter.status()}\n"
            f"  {self.token_limiter.status()}"
        )


def demonstrate_token_bucket() -> None:
    """
    トークンバケットアルゴリズムのデモ（APIなし）
    """
    print("\n--- トークンバケットアルゴリズムのデモ ---")

    # 1秒あたり2リクエスト、最大バースト5リクエスト
    limiter = TokenBucketRateLimiter(capacity=5, refill_rate=2, name="demo")

    print(f"初期状態: {limiter.status()}")
    print()

    # バーストリクエスト（最初の5つは即座に処理）
    print("連続5リクエスト（バーストの利用）:")
    for i in range(5):
        start = time.time()
        success = limiter.acquire()
        elapsed = time.time() - start
        print(f"  リクエスト {i+1}: {'✅ 成功' if success else '❌ 失敗'} "
              f"（{elapsed*1000:.0f}ms待機、残りトークン: {limiter.tokens:.1f}）")

    print(f"\n5リクエスト後の状態: {limiter.status()}")

    # 6番目のリクエスト（補充を待つ）
    print("\n6番目のリクエスト（補充待ち）:")
    start = time.time()
    success = limiter.acquire()
    elapsed = time.time() - start
    print(f"  リクエスト 6: {'✅ 成功' if success else '❌ 失敗'} "
          f"（{elapsed*1000:.0f}ms待機）")

    print(f"\n{limiter.stats.summary()}")


def demonstrate_rate_limited_client(client: Anthropic) -> None:
    """
    レート制限付きAPIクライアントのデモ

    Args:
        client: Anthropicクライアント
    """
    print("\n--- レート制限付きAPIクライアントのデモ ---")

    # 低いレート制限でデモ（実際の使用では適切な値を設定）
    rate_limited_client = RateLimitedAPIClient(
        client=client,
        rpm_limit=60,    # 1分60リクエスト
        tpm_limit=100000  # 1分100,000トークン
    )

    print(rate_limited_client.status())
    print()

    # 複数のリクエストを送信
    questions = [
        "Pythonとは何ですか？一文で答えてください。",
        "機械学習とは何ですか？一文で答えてください。",
        "APIとは何ですか？一文で答えてください。",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\nリクエスト {i}: {question}")
        result = rate_limited_client.create_message(
            messages=[{"role": "user", "content": question}],
            max_tokens=100
        )
        if result:
            print(f"  応答: {result}")


def rate_limiting_best_practices() -> None:
    """
    レート制限のベストプラクティスを表示する
    """
    print("\n--- レート制限のベストプラクティス ---")

    best_practices = """
【✅ レート制限実装のポイント】

1. 事前にレート制限を実装する（プロアクティブ）
   - APIからの429エラーを待つのではなく、事前に制限する
   - ユーザー体験が向上し、エラーハンドリングが単純になる

2. アルゴリズムの選択
   - トークンバケット: バーストを許可しつつ平均レートを制限
   - スライディングウィンドウ: より正確な制限、メモリ使用量が多い
   - 固定ウィンドウ: シンプルだが境界付近でバーストが起きる可能性

3. スレッドセーフな実装
   - threading.Lock() を使って排他制御する
   - マルチスレッド環境では必須

4. RPMとTPMの両方を管理する
   - RPM（リクエスト数）とTPM（トークン数）は独立して制限が必要
   - Anthropic APIは両方の制限がある

5. 余裕を持った設定
   - API制限の80〜90%程度で自己制限を設定する
   - バースト的なトラフィックへの余裕を持たせる

6. 429エラーの処理
   - retry-after ヘッダーの値を使って待機時間を設定する
   - Exponential backoff と組み合わせる

【⚠️ よくある間違い】

1. レート制限なし → 429エラーが多発する
2. グローバルな状態管理漏れ → マルチスレッドで正確に動作しない
3. TPM（トークン数）の無視 → RPMのみを制限してもTPM超過が発生
4. 制限値をぎりぎりに設定 → わずかな変動で制限超過が起きる

【💡 CCA試験のポイント】
- Anthropic API には RPM と TPM の両方の制限がある
- トークンバケットアルゴリズムは面接でよく出る設計問題
- 429 は「Too Many Requests」= レート制限超過
- retry-after ヘッダーには次のリクエストまでの待機秒数が含まれる
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 60)
    print("レート制限の実装")
    print("=" * 60)

    # トークンバケットのデモ（APIなし）
    demonstrate_token_bucket()

    # ベストプラクティスの表示（APIなし）
    rate_limiting_best_practices()

    # APIを使ったデモ
    print("\n--- API接続テスト ---")
    client = get_client()
    demonstrate_rate_limited_client(client)

    print("\n✅ 完了！次は05_token_management.pyに進んでください。")
