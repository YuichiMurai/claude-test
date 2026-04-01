"""
exercise_01.py - 練習問題1: 高性能APIクライアントの設計

難易度: ⭐⭐⭐⭐ 上級

目的:
キャッシング、非同期処理、エラーハンドリングを組み合わせた
高性能なAPIクライアントを実装する。

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv nest_asyncio -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. Colabでの非同期実行:
   import nest_asyncio
   nest_asyncio.apply()

4. このファイルの内容をColabのセルに貼り付けて実行

【実装する機能】
1. TTL付きLRUキャッシュ
2. 非同期並行処理（asyncio.gather + Semaphore）
3. Exponential backoff リトライ
4. パフォーマンス測定

【参考ファイル】
- 04_architecture/01_caching_strategy.py - キャッシング実装
- 04_architecture/02_async_processing.py - 非同期処理
- 03_secure_applications/03_error_handling.py - エラーハンドリング
"""

import asyncio
import hashlib
import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional

import anthropic  # noqa: F401 - students will use anthropic.RateLimitError etc. in their implementation
from anthropic import AsyncAnthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"


def get_async_client() -> AsyncAnthropic:
    """非同期APIクライアントを取得する（Colab・ローカル両対応）"""
    try:
        from google.colab import userdata
        api_key = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')

    return AsyncAnthropic(api_key=api_key)


# =============================================================================
# TODO 1: キャッシュエントリのデータクラスを実装する
# =============================================================================

@dataclass
class CacheEntry:
    """
    キャッシュエントリ

    Attributes:
        value: キャッシュされた値
        created_at: 作成時刻
        ttl: 有効期限（秒）。0以下で無期限
    """
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: float = 0.0

    def is_expired(self) -> bool:
        """
        TODO 1-1: TTL切れかどうかを確認するメソッドを実装する

        条件:
        - ttl が 0 以下の場合: 常に False を返す（無期限）
        - ttl が 0 より大きい場合: 現在時刻 - 作成時刻 > ttl なら True

        Returns:
            bool: 期限切れなら True
        """
        # TODO: ここを実装してください
        pass  # 削除してください


# =============================================================================
# TODO 2: TTL付きLRUキャッシュを実装する
# =============================================================================

class HighPerformanceCache:
    """
    TTL付きLRUキャッシュ

    【ヒント】
    - OrderedDict を使ってLRU順序を管理する
    - get() でアクセス時に move_to_end() で最近使用済みにする
    - set() でサイズ超過時に先頭（最も古い）エントリを削除する
    """

    def __init__(self, maxsize: int = 128, default_ttl: float = 300.0):
        """
        Args:
            maxsize: 最大キャッシュ数
            default_ttl: デフォルトTTL（秒）
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def make_key(self, **kwargs: Any) -> str:
        """
        キャッシュキーを生成する

        Args:
            **kwargs: キーとなるパラメータ

        Returns:
            str: SHA-256ハッシュ文字列
        """
        key_str = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        TODO 2-1: キャッシュから値を取得する

        手順:
        1. key が _cache にない場合: _misses を増やして None を返す
        2. エントリが期限切れの場合: 削除して _misses を増やして None を返す
        3. LRU更新: move_to_end(key) で最近使用済みにする
        4. _hits を増やして値を返す

        Returns:
            Optional[Any]: キャッシュ値（なければNone）
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        TODO 2-2: キャッシュに値を保存する

        手順:
        1. ttl が None の場合は default_ttl を使用
        2. key が既存の場合は move_to_end(key) で更新
        3. CacheEntry を作成して _cache に保存
        4. サイズが maxsize を超えた場合は先頭エントリを削除（LRU削除）
           ヒント: self._cache.popitem(last=False) で先頭を削除

        Args:
            key: キャッシュキー
            value: 保存する値
            ttl: TTL（秒）
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    @property
    def hit_rate(self) -> float:
        """キャッシュヒット率（0.0〜1.0）"""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict:
        """キャッシュ統計"""
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
        }


# =============================================================================
# TODO 3: 非同期処理でリトライを実装する
# =============================================================================

async def async_query_with_retry(
    client: AsyncAnthropic,
    prompt: str,
    cache: HighPerformanceCache,
    max_tokens: int = 200,
    max_retries: int = 3,
    semaphore: Optional[asyncio.Semaphore] = None
) -> dict:
    """
    TODO 3: キャッシング + リトライ付き非同期クエリ

    実装手順:
    1. キャッシュキーを生成する（cache.make_key を使用）
    2. キャッシュを確認する。HIT なら即座に返す
    3. semaphore があれば async with semaphore: で囲む
    4. Exponential backoff でリトライ（最大 max_retries 回）:
       - attempt 0: 即座に実行
       - attempt 1以降: 2^(attempt-1) 秒待機してからリトライ
    5. 成功したらキャッシュに保存して返す

    【ヒント】
    バックオフ計算: delay = 2 ** attempt（1秒、2秒、4秒...）
    anthropic.RateLimitError と anthropic.InternalServerError はリトライ対象

    Args:
        client: 非同期APIクライアント
        prompt: プロンプト
        cache: キャッシュインスタンス
        max_tokens: 最大トークン数
        max_retries: 最大リトライ回数
        semaphore: 同時実行数制御のSemaphore

    Returns:
        dict: {
            "text": レスポンステキスト,
            "from_cache": キャッシュから返したか,
            "elapsed": 処理時間（秒）,
            "attempts": 試行回数
        }
    """
    # TODO: ここを実装してください

    # ヒント: 以下の構造を参考にしてください
    # cache_key = cache.make_key(prompt=prompt, max_tokens=max_tokens)
    # cached = cache.get(cache_key)
    # if cached:
    #     return {"text": cached, "from_cache": True, "elapsed": ..., "attempts": 0}
    #
    # async def _execute():
    #     for attempt in range(max_retries + 1):
    #         try:
    #             response = await client.messages.create(...)
    #             return response.content[0].text
    #         except (anthropic.RateLimitError, anthropic.InternalServerError) as e:
    #             if attempt < max_retries:
    #                 await asyncio.sleep(2 ** attempt)
    #             else:
    #                 raise
    #
    # if semaphore:
    #     async with semaphore:
    #         text = await _execute()
    # else:
    #     text = await _execute()
    #
    # cache.set(cache_key, text)
    # return {"text": text, "from_cache": False, "elapsed": ..., "attempts": ...}
    pass  # 削除してください


# =============================================================================
# TODO 4: 高性能クライアントのメインクラスを完成させる
# =============================================================================

class HighPerformanceAPIClient:
    """
    高性能APIクライアント

    キャッシング + 非同期並行処理 + リトライを統合したクライアント。
    """

    def __init__(
        self,
        cache_maxsize: int = 128,
        cache_ttl: float = 300.0,
        max_concurrent: int = 5,
        max_retries: int = 3
    ):
        self.client = get_async_client()
        self.cache = HighPerformanceCache(maxsize=cache_maxsize, default_ttl=cache_ttl)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_retries = max_retries
        self._total_requests = 0

    async def query(self, prompt: str, max_tokens: int = 200) -> dict:
        """
        単一クエリを実行する

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            dict: クエリ結果
        """
        self._total_requests += 1
        return await async_query_with_retry(
            self.client, prompt, self.cache,
            max_tokens=max_tokens,
            max_retries=self.max_retries,
            semaphore=self.semaphore
        )

    async def batch_query(
        self, prompts: list[str], max_tokens: int = 200
    ) -> list[dict]:
        """
        TODO 4: 複数プロンプトを並行処理する

        asyncio.gather() を使って prompts のすべてを並行実行してください。

        Args:
            prompts: プロンプトのリスト
            max_tokens: 最大トークン数

        Returns:
            list[dict]: 各クエリの結果
        """
        # TODO: asyncio.gather() を使って実装してください
        pass  # 削除してください

    def print_performance_stats(self) -> None:
        """パフォーマンス統計を表示する"""
        stats = self.cache.stats
        print("\n" + "=" * 50)
        print("📊 パフォーマンスサマリー")
        print("=" * 50)
        print(f"総リクエスト数: {self._total_requests}")
        print(f"キャッシュHIT数: {stats['hits']}")
        print(f"APIコール数: {stats['misses']}")
        print(f"キャッシュヒット率: {stats['hit_rate'] * 100:.1f}%")
        print("=" * 50)


# =============================================================================
# メイン関数
# =============================================================================

async def main() -> None:
    """
    高性能APIクライアントのデモ
    """
    print("=" * 60)
    print("練習問題1: 高性能APIクライアント")
    print("=" * 60)

    client = HighPerformanceAPIClient(
        cache_maxsize=64,
        cache_ttl=300.0,
        max_concurrent=3,
        max_retries=2
    )

    # テスト1: キャッシュのテスト
    print("\n[テスト1: キャッシュ動作の確認]")
    prompt = "Pythonとは？1文で答えてください。"

    result1 = await client.query(prompt, max_tokens=100)
    if result1:
        print(f"1回目: {result1.get('elapsed', 0):.3f}秒 "
              f"[{'キャッシュHIT' if result1.get('from_cache') else 'API呼び出し'}]")
        print(f"  → {(result1.get('text') or '')[:60]}...")

    result2 = await client.query(prompt, max_tokens=100)
    if result2:
        print(f"2回目: {result2.get('elapsed', 0):.4f}秒 "
              f"[{'キャッシュHIT' if result2.get('from_cache') else 'API呼び出し'}]")

    # テスト2: 並行処理のテスト
    print("\n[テスト2: 並行処理]")
    test_prompts = [
        "Javaとは？1文で。",
        "JavaScriptとは？1文で。",
        "Goとは？1文で。",
        "Rustとは？1文で。",
        "Kotlinとは？1文で。",
    ]

    start_seq = time.time()
    for p in test_prompts:
        await client.query(p, max_tokens=50)
    seq_time = time.time() - start_seq
    print(f"逐次処理（参考）: {seq_time:.3f}秒（{len(test_prompts)}件）")

    # キャッシュをクリアして並行処理を実測
    client.cache._cache.clear()
    client.cache._hits = 0
    client.cache._misses = 0

    start_con = time.time()
    results = await client.batch_query(test_prompts, max_tokens=50)
    con_time = time.time() - start_con
    print(f"並行処理: {con_time:.3f}秒（{len(test_prompts)}件）")
    if results and seq_time > 0 and con_time > 0:
        print(f"速度改善: {seq_time / con_time:.1f}倍速")

    # パフォーマンス統計の表示
    client.print_performance_stats()

    print("\n✅ 完了！次はexercise_02.pyに進んでください。")


if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass

    asyncio.run(main())
