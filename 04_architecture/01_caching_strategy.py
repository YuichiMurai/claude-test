"""
01_caching_strategy.py - キャッシング戦略

このファイルの目的:
- LRUキャッシュを使ってAPIコールを最適化する方法を学ぶ
- TTL（Time To Live）付きキャッシュの実装を理解する
- キャッシュキーの設計方法を習得する
- キャッシュ無効化の戦略を理解する
- キャッシュヒット率の測定方法を学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 04_architecture/01_caching_strategy.py

【キャッシングが重要な理由】
同じプロンプトに対して毎回APIを呼び出すとコストが増大します。
キャッシングによって:
- APIコストを大幅削減できる
- レスポンス速度が向上する
- レート制限を守りやすくなる
- システム全体の安定性が向上する
"""

import hashlib
import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Optional

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
# 1. LRUキャッシュの実装（functoolsのlru_cacheを使用）
# =============================================================================

@lru_cache(maxsize=128)
def cached_simple_query(prompt: str, max_tokens: int = 512) -> str:
    """
    lru_cache デコレータを使ったシンプルなキャッシュ実装

    同じ引数で呼び出された場合、前回の結果を再利用します。
    maxsize=128 は最大128件のキャッシュを保持することを意味します。

    注意: この関数はAPIクライアントを内部で生成するため、
    引数が同じであれば必ず同じ結果を返します。

    Args:
        prompt: ユーザーのプロンプト
        max_tokens: 最大トークン数

    Returns:
        str: APIレスポンス（またはキャッシュされた結果）
    """
    # この関数はキャッシュが有効なときは呼ばれない
    # キャッシュが無効なときだけAPIを呼び出す
    client = get_client()
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def demonstrate_lru_cache() -> None:
    """
    lru_cache の動作をデモする

    同じプロンプトで2回呼び出すと、2回目はキャッシュから返ることを確認する。
    """
    print("\n--- 1. LRUキャッシュのデモ（functools.lru_cache） ---")
    prompt = "Pythonのリスト内包表記とは何ですか？1文で答えてください。"

    # 1回目: APIを呼び出す（キャッシュなし）
    print(f"プロンプト: {prompt}")
    start = time.time()
    result1 = cached_simple_query(prompt, max_tokens=100)
    elapsed1 = time.time() - start
    print(f"1回目: {elapsed1:.3f}秒 → {result1[:60]}...")

    # 2回目: キャッシュから返る（APIを呼び出さない）
    start = time.time()
    cached_simple_query(prompt, max_tokens=100)
    elapsed2 = time.time() - start
    print(f"2回目: {elapsed2:.3f}秒 → キャッシュから返却")

    # キャッシュ統計を表示
    cache_info = cached_simple_query.cache_info()
    print("\nキャッシュ統計:")
    print(f"  ヒット数: {cache_info.hits}")
    print(f"  ミス数: {cache_info.misses}")
    print(f"  現在のキャッシュ数: {cache_info.currsize}")
    print(f"  最大キャッシュ数: {cache_info.maxsize}")
    print(f"  ヒット率: {cache_info.hits / (cache_info.hits + cache_info.misses) * 100:.1f}%")
    print(f"\n速度改善: {elapsed1:.3f}秒 → {elapsed2:.3f}秒 "
          f"（{elapsed1 / max(elapsed2, 0.0001):.0f}倍速）")


# =============================================================================
# 2. カスタムキャッシュ実装（TTL付きLRUキャッシュ）
# =============================================================================

@dataclass
class CacheEntry:
    """
    キャッシュエントリ（値 + メタデータ）

    Attributes:
        value: キャッシュされた値
        created_at: エントリ作成時刻（UNIXタイムスタンプ）
        ttl: 有効期限（秒）。0以下の場合は無期限
        hit_count: このエントリへのアクセス回数
    """
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: float = 0.0
    hit_count: int = 0

    def is_expired(self) -> bool:
        """TTLが設定されており、有効期限切れかどうかを確認する"""
        if self.ttl <= 0:
            return False  # TTL未設定 = 無期限
        return time.time() - self.created_at > self.ttl


class TTLLRUCache:
    """
    TTL（Time To Live）付きLRUキャッシュ

    LRU（Least Recently Used）アルゴリズムと
    TTLによる自動失効を組み合わせたキャッシュ実装。

    【LRUとは】
    最も長い間使われていないアイテムを削除する戦略。
    - キャッシュが満杯になると、最も古く使われていないアイテムを削除
    - 最近使われたアイテムは優先的に保持される
    - OrderedDict を使って実装するのが一般的

    Attributes:
        maxsize: 最大キャッシュ数
        default_ttl: デフォルトのTTL（秒）
    """

    def __init__(self, maxsize: int = 128, default_ttl: float = 300.0):
        """
        Args:
            maxsize: 最大キャッシュ数
            default_ttl: デフォルトのTTL（秒）。0以下で無期限
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        # OrderedDict: 挿入順序を保持するdict（Python 3.7+）
        # ここでは「最近アクセスされた順」を管理するために使用
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0    # キャッシュヒット数
        self._misses = 0  # キャッシュミス数

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """
        キャッシュキーを生成する

        引数をJSON文字列に変換してSHA-256ハッシュを計算。
        同じ引数には同じキーが生成されることを保証する。

        Args:
            *args: 位置引数
            **kwargs: キーワード引数

        Returns:
            str: ハッシュ文字列（16進数64文字）
        """
        # 引数をJSONシリアライズ可能な形式に変換
        key_data = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        # SHA-256でハッシュ化（衝突を防ぐ）
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから値を取得する

        Args:
            key: キャッシュキー

        Returns:
            Optional[Any]: キャッシュされた値。存在しないまたは期限切れの場合はNone
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # TTL切れチェック
        if entry.is_expired():
            # 期限切れのエントリを削除
            del self._cache[key]
            self._misses += 1
            return None

        # LRU更新: このエントリを最近使用済みとしてマーク
        self._cache.move_to_end(key)
        entry.hit_count += 1
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        キャッシュに値を保存する

        Args:
            key: キャッシュキー
            value: 保存する値
            ttl: 有効期限（秒）。Noneの場合はdefault_ttlを使用
        """
        effective_ttl = ttl if ttl is not None else self.default_ttl

        # 既存エントリを更新する場合は末尾に移動
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = CacheEntry(
            value=value,
            ttl=effective_ttl
        )

        # キャッシュサイズ制限のチェック
        # 超過した場合は最も古い（最も長く使われていない）エントリを削除
        while len(self._cache) > self.maxsize:
            # OrderedDict の先頭が最も古いエントリ
            oldest_key, _ = self._cache.popitem(last=False)
            # last=False で先頭から削除（LRU削除）

    def invalidate(self, key: str) -> bool:
        """
        特定のキーのキャッシュを無効化する

        Args:
            key: 削除するキャッシュキー

        Returns:
            bool: 削除成功したかどうか
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        パターンマッチでキャッシュを一括無効化する

        Args:
            pattern: 削除するキーのパターン（部分一致）

        Returns:
            int: 削除したエントリ数
        """
        keys_to_delete = [k for k in self._cache if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)

    def clear(self) -> None:
        """キャッシュを全削除する"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict:
        """キャッシュの統計情報を返す"""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }

    def __len__(self) -> int:
        return len(self._cache)


# =============================================================================
# 3. キャッシング付きAPIクライアント
# =============================================================================

class CachingAPIClient:
    """
    キャッシング機能を持つAPIクライアント

    同一のリクエストに対してキャッシュを活用し、
    APIコールを最小化します。

    Attributes:
        client: Anthropicクライアント
        cache: TTL付きLRUキャッシュ
    """

    def __init__(self, maxsize: int = 128, ttl: float = 300.0):
        """
        Args:
            maxsize: 最大キャッシュエントリ数
            ttl: キャッシュの有効期限（秒）。デフォルト5分
        """
        self.client = get_client()
        self.cache = TTLLRUCache(maxsize=maxsize, default_ttl=ttl)
        self._api_calls = 0      # 実際のAPIコール数
        self._total_requests = 0  # 総リクエスト数

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 512,
        use_cache: bool = True,
        ttl: Optional[float] = None
    ) -> dict:
        """
        キャッシング付きのAPIクエリ

        Args:
            prompt: ユーザーのプロンプト
            system: システムプロンプト（オプション）
            max_tokens: 最大トークン数
            use_cache: キャッシュを使用するか
            ttl: このリクエスト固有のTTL（秒）

        Returns:
            dict: {
                "text": レスポンステキスト,
                "from_cache": キャッシュから返したか,
                "elapsed": レスポンスタイム（秒）
            }
        """
        self._total_requests += 1

        # キャッシュキーを生成
        cache_key = self.cache._make_key(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens
        )

        start = time.time()

        # キャッシュを確認
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return {
                    "text": cached,
                    "from_cache": True,
                    "elapsed": time.time() - start
                }

        # APIを呼び出す
        self._api_calls += 1
        params: dict[str, Any] = {
            "model": MODEL_NAME,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system:
            params["system"] = system

        response = self.client.messages.create(**params)
        text = response.content[0].text
        elapsed = time.time() - start

        # キャッシュに保存
        if use_cache:
            self.cache.set(cache_key, text, ttl=ttl)

        return {
            "text": text,
            "from_cache": False,
            "elapsed": elapsed
        }

    def invalidate_cache(self, prompt: str, system: Optional[str] = None,
                         max_tokens: int = 512) -> bool:
        """
        特定のリクエストのキャッシュを無効化する

        Args:
            prompt: 無効化するプロンプト
            system: システムプロンプト
            max_tokens: 最大トークン数

        Returns:
            bool: 無効化に成功したか
        """
        cache_key = self.cache._make_key(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens
        )
        return self.cache.invalidate(cache_key)

    @property
    def efficiency_stats(self) -> dict:
        """効率統計を返す"""
        saved_calls = self._total_requests - self._api_calls
        return {
            "total_requests": self._total_requests,
            "api_calls": self._api_calls,
            "cache_hits": saved_calls,
            "api_call_reduction": saved_calls / self._total_requests if self._total_requests > 0 else 0.0,
            **self.cache.stats
        }


# =============================================================================
# 4. デモ関数
# =============================================================================

def demonstrate_ttl_cache(client: CachingAPIClient) -> None:
    """
    TTL付きキャッシュのデモ

    Args:
        client: キャッシング付きAPIクライアント
    """
    print("\n--- 2. TTL付きLRUキャッシュのデモ ---")
    prompt = "Pythonの辞書型（dict）の特徴を1文で説明してください。"

    print(f"プロンプト: {prompt}")
    print()

    # 1回目: APIを呼び出す
    result1 = client.query(prompt, max_tokens=100, ttl=5.0)
    print(f"1回目: {result1['elapsed']:.3f}秒 "
          f"[{'キャッシュHIT' if result1['from_cache'] else 'API呼び出し'}]")
    print(f"  → {result1['text'][:60]}...")

    # 2回目: キャッシュから返る
    result2 = client.query(prompt, max_tokens=100)
    print(f"2回目: {result2['elapsed']:.4f}秒 "
          f"[{'キャッシュHIT' if result2['from_cache'] else 'API呼び出し'}]")
    print("  → キャッシュから返却（同じ結果）")

    # 3回目: キャッシュを無効化してから呼び出す
    client.invalidate_cache(prompt, max_tokens=100)
    result3 = client.query(prompt, max_tokens=100)
    print(f"3回目（無効化後）: {result3['elapsed']:.3f}秒 "
          f"[{'キャッシュHIT' if result3['from_cache'] else 'API呼び出し'}]")
    print("  → キャッシュを無効化したのでAPIを呼び出し")


def demonstrate_cache_hit_rate(client: CachingAPIClient) -> None:
    """
    キャッシュヒット率の測定デモ

    複数のプロンプトで一部を繰り返し呼び出し、ヒット率を測定する。

    Args:
        client: キャッシング付きAPIクライアント
    """
    print("\n--- 3. キャッシュヒット率の測定 ---")

    # テスト用のプロンプトセット（一部を繰り返す）
    prompts = [
        "Pythonとは？1文で。",      # 1回目
        "Javaとは？1文で。",         # 1回目
        "Pythonとは？1文で。",       # 2回目（キャッシュHIT）
        "JavaScriptとは？1文で。",   # 1回目
        "Javaとは？1文で。",          # 2回目（キャッシュHIT）
        "Pythonとは？1文で。",       # 3回目（キャッシュHIT）
    ]

    print(f"{'番号':<5} {'プロンプト':<25} {'結果':<15} {'時間':<10}")
    print("-" * 55)

    for i, prompt in enumerate(prompts, 1):
        result = client.query(prompt, max_tokens=50)
        status = "キャッシュHIT" if result["from_cache"] else "API呼び出し"
        print(f"{i:<5} {prompt[:23]:<25} {status:<15} {result['elapsed']:.4f}秒")

    # 統計表示
    stats = client.efficiency_stats
    print("\nキャッシュ統計:")
    print(f"  総リクエスト数: {stats['total_requests']}")
    print(f"  実際のAPIコール数: {stats['api_calls']}")
    print(f"  キャッシュHIT数: {stats['cache_hits']}")
    print(f"  APIコール削減率: {stats['api_call_reduction'] * 100:.1f}%")
    print(f"  キャッシュヒット率: {stats['hit_rate'] * 100:.1f}%")


def caching_best_practices() -> None:
    """キャッシング戦略のベストプラクティスを表示する"""
    print("\n--- キャッシング戦略のベストプラクティス ---")

    best_practices = """
【✅ キャッシングのポイント】

1. キャッシュキーの設計
   - プロンプト、システムプロンプト、パラメータをすべて含める
   - ハッシュ関数（SHA-256など）でキーを固定長に
   - 大文字小文字の正規化など、同等なリクエストは同じキーに

2. TTLの設定
   - 変化しない知識（FAQ等）: 長めのTTL（1時間〜24時間）
   - 動的なコンテンツ: 短いTTL（5分〜30分）
   - リアルタイム情報: TTLなし（キャッシュしない）

3. キャッシュ無効化のタイミング
   - データが更新された直後
   - TTLが切れたとき（自動）
   - ユーザーが明示的に「更新」を要求したとき

4. メモリ管理
   - maxsize を適切に設定（メモリと効果のトレードオフ）
   - LRUアルゴリズムで古いエントリを自動削除
   - 定期的にキャッシュ統計を確認して調整する

5. キャッシュできないケース
   - ユーザー固有の会話（personalized content）
   - リアルタイムデータ（株価、天気など）
   - セキュリティ上機密なデータ

【💡 CCA試験のポイント】
- LRU = Least Recently Used（最も長く使われていないものを削除）
- TTL = Time To Live（有効期限。超えたら自動削除）
- キャッシュヒット率 = ヒット数 / (ヒット数 + ミス数) × 100%
- functools.lru_cache は関数レベルのキャッシュに最適
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 60)
    print("キャッシング戦略")
    print("=" * 60)

    # ベストプラクティスの表示（APIなし）
    caching_best_practices()

    # APIクライアントを初期化
    print("\n--- API接続テスト ---")
    caching_client = CachingAPIClient(maxsize=64, ttl=300.0)

    # 1. lru_cache デコレータのデモ
    demonstrate_lru_cache()

    # 2. TTL付きLRUキャッシュのデモ
    demonstrate_ttl_cache(caching_client)

    # 3. キャッシュヒット率の測定
    demonstrate_cache_hit_rate(caching_client)

    print("\n✅ 完了！次は02_async_processing.pyに進んでください。")
