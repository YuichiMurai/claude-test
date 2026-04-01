"""
03_error_handling.py - エラーハンドリングとリトライロジック

このファイルの目的:
- Claude API が返す各種エラーの種類と対処方法を学ぶ
- Exponential backoff によるリトライ実装を理解する
- タイムアウト処理の実装方法を習得する
- フォールバック戦略の設計パターンを学ぶ
- ロギングのベストプラクティスを習得する

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 03_secure_applications/03_error_handling.py

【エラーハンドリングが重要な理由】
本番環境では、APIエラーは必ず発生します。
適切なエラーハンドリングにより:
- ユーザーへの影響を最小化できる
- 自動回復（リトライ）で可用性を向上できる
- デバッグのためのログを残せる
- コスト爆発（無限リトライなど）を防げる
"""

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Optional

import anthropic
from anthropic import Anthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"

# ロギングの設定
# Google Colab では basicConfig でコンソール出力を設定する
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# リトライのパラメータ
MAX_RETRIES = 3          # 最大リトライ回数
BASE_DELAY = 1.0         # 初期待機時間（秒）
MAX_DELAY = 60.0         # 最大待機時間（秒）
BACKOFF_FACTOR = 2.0     # 指数バックオフの倍率
REQUEST_TIMEOUT = 30     # リクエストタイムアウト（秒）


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


def calculate_backoff_delay(attempt: int, base_delay: float = BASE_DELAY,
                             max_delay: float = MAX_DELAY,
                             backoff_factor: float = BACKOFF_FACTOR) -> float:
    """
    Exponential backoff の待機時間を計算する

    計算式: min(base_delay * (backoff_factor ^ attempt), max_delay)

    例（デフォルト設定の場合）:
    - 1回目: 1.0 * 2^0 = 1.0秒
    - 2回目: 1.0 * 2^1 = 2.0秒
    - 3回目: 1.0 * 2^2 = 4.0秒
    - 4回目: 1.0 * 2^3 = 8.0秒（max_delayでキャップされる）

    Args:
        attempt: 現在の試行回数（0から始まる）
        base_delay: 基本待機時間（秒）
        max_delay: 最大待機時間（秒）
        backoff_factor: バックオフ倍率

    Returns:
        float: 待機時間（秒）
    """
    delay = base_delay * (backoff_factor ** attempt)
    return min(delay, max_delay)


def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
    retryable_status_codes: Optional[list[int]] = None
) -> Any:
    """
    Exponential backoff でリトライを行うラッパー関数

    リトライ対象のエラー:
    - 429 Too Many Requests（レート制限）
    - 500 Internal Server Error（一時的なサーバーエラー）
    - 529 Overloaded（APIサーバー過負荷）

    リトライしないエラー:
    - 400 Bad Request（リクエスト自体が不正）
    - 401 Unauthorized（認証エラー）
    - 403 Forbidden（権限エラー）
    - 404 Not Found（リソースが存在しない）

    Args:
        func: リトライする関数
        max_retries: 最大リトライ回数
        base_delay: 基本待機時間（秒）
        retryable_status_codes: リトライ対象のHTTPステータスコード

    Returns:
        Any: 関数の戻り値

    Raises:
        Exception: 最大リトライ回数を超えた場合
    """
    # リトライ対象のステータスコード（デフォルト）
    if retryable_status_codes is None:
        retryable_status_codes = [429, 500, 502, 503, 529]

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()

        except anthropic.RateLimitError as e:
            # 429: レート制限エラー
            last_exception = e
            if attempt < max_retries:
                delay = calculate_backoff_delay(attempt, base_delay)
                logger.warning(
                    f"レート制限エラー（429）。{delay:.1f}秒後にリトライします "
                    f"（{attempt + 1}/{max_retries}回目）: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(f"最大リトライ回数（{max_retries}）を超えました: {e}")
                raise

        except anthropic.InternalServerError as e:
            # 500/529: サーバーエラー・過負荷
            last_exception = e
            if attempt < max_retries:
                delay = calculate_backoff_delay(attempt, base_delay)
                logger.warning(
                    f"サーバーエラー（{e.status_code}）。{delay:.1f}秒後にリトライします "
                    f"（{attempt + 1}/{max_retries}回目）: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(f"最大リトライ回数（{max_retries}）を超えました: {e}")
                raise

        except anthropic.APIStatusError as e:
            # その他のAPIエラー（ステータスコードでリトライ判断）
            last_exception = e
            if e.status_code in retryable_status_codes and attempt < max_retries:
                delay = calculate_backoff_delay(attempt, base_delay)
                logger.warning(
                    f"APIエラー（{e.status_code}）。{delay:.1f}秒後にリトライします "
                    f"（{attempt + 1}/{max_retries}回目）: {e}"
                )
                time.sleep(delay)
            else:
                # リトライ不可能なエラー（400, 401, 403など）は即座に再raise
                logger.error(f"リトライ不可能なAPIエラー（{e.status_code}）: {e}")
                raise

        except anthropic.APIConnectionError as e:
            # ネットワーク接続エラー
            last_exception = e
            if attempt < max_retries:
                delay = calculate_backoff_delay(attempt, base_delay)
                logger.warning(
                    f"接続エラー。{delay:.1f}秒後にリトライします "
                    f"（{attempt + 1}/{max_retries}回目）: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(f"接続エラーが継続しています: {e}")
                raise

        except anthropic.APITimeoutError as e:
            # タイムアウトエラー
            last_exception = e
            if attempt < max_retries:
                delay = calculate_backoff_delay(attempt, base_delay)
                logger.warning(
                    f"タイムアウト。{delay:.1f}秒後にリトライします "
                    f"（{attempt + 1}/{max_retries}回目）: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(f"タイムアウトが継続しています: {e}")
                raise

    # ここには通常到達しないが、念のため
    if last_exception:
        raise last_exception
    raise RuntimeError("予期しないエラー: リトライループが正常に終了しませんでした")


def api_call_with_retry(
    client: Anthropic,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 512,
    max_retries: int = MAX_RETRIES
) -> Optional[str]:
    """
    リトライ機能付きAPIコール関数

    Args:
        client: Anthropicクライアント
        messages: メッセージリスト
        system: システムプロンプト（オプション）
        max_tokens: 最大トークン数
        max_retries: 最大リトライ回数

    Returns:
        Optional[str]: レスポンステキスト、失敗時はNone
    """
    request_params: dict[str, Any] = {
        "model": MODEL_NAME,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        request_params["system"] = system

    def _make_request() -> str:
        response = client.messages.create(**request_params)
        return response.content[0].text

    try:
        return retry_with_exponential_backoff(_make_request, max_retries=max_retries)
    except Exception as e:
        logger.error(f"APIコールが失敗しました: {e}")
        return None


def api_call_with_fallback(
    client: Anthropic,
    messages: list[dict],
    fallback_message: str = "申し訳ございませんが、現在サービスが利用できません。しばらくしてからお試しください。"
) -> str:
    """
    フォールバック付きAPIコール関数

    APIが使用できない場合でも、ユーザーに適切なメッセージを返します。

    Args:
        client: Anthropicクライアント
        messages: メッセージリスト
        fallback_message: フォールバックメッセージ

    Returns:
        str: レスポンステキスト、またはフォールバックメッセージ
    """
    result = api_call_with_retry(client, messages)
    if result is None:
        logger.warning("APIコールが失敗したため、フォールバックメッセージを返します")
        return fallback_message
    return result


def demonstrate_error_types() -> None:
    """
    Claude APIのエラータイプを解説する（APIなし）
    """
    print("\n--- Claude APIのエラータイプ ---")

    error_types = """
【Claude API のエラータイプ一覧】

1. anthropic.AuthenticationError (401)
   - 原因: APIキーが無効または存在しない
   - 対処: APIキーを確認・更新する
   - リトライ: ❌ 不要（リトライしても解決しない）

2. anthropic.PermissionDeniedError (403)
   - 原因: そのリソースへのアクセス権限がない
   - 対処: Anthropicアカウントの権限を確認する
   - リトライ: ❌ 不要

3. anthropic.NotFoundError (404)
   - 原因: 指定したモデルやリソースが存在しない
   - 対処: モデル名などのパラメータを確認する
   - リトライ: ❌ 不要

4. anthropic.UnprocessableEntityError (422)
   - 原因: リクエストの形式が正しくない
   - 対処: リクエストパラメータを確認する
   - リトライ: ❌ 不要

5. anthropic.RateLimitError (429)
   - 原因: APIのレート制限を超過した
   - 対処: 待機してからリトライする
   - リトライ: ✅ 必要（Exponential backoffで）
   - ヘッダー: retry-after ヘッダーに待機時間が含まれる場合あり

6. anthropic.InternalServerError (500)
   - 原因: Anthropic側のサーバーエラー
   - 対処: しばらく待機してからリトライする
   - リトライ: ✅ 必要

7. anthropic.InternalServerError (529) - Overloaded
   - 原因: APIサーバーの過負荷
   - 対処: より長い待機時間でリトライする
   - リトライ: ✅ 必要

8. anthropic.APIConnectionError
   - 原因: ネットワーク接続エラー
   - 対処: ネットワーク環境を確認し、リトライする
   - リトライ: ✅ 必要

9. anthropic.APITimeoutError
   - 原因: リクエストがタイムアウトした
   - 対処: max_tokensを小さくするか、より短いプロンプトを使う
   - リトライ: ✅ 条件付きで必要

【継承関係】
anthropic.APIError（基底クラス）
├── anthropic.APIStatusError（HTTPステータスエラー）
│   ├── anthropic.AuthenticationError (401)
│   ├── anthropic.PermissionDeniedError (403)
│   ├── anthropic.NotFoundError (404)
│   ├── anthropic.UnprocessableEntityError (422)
│   ├── anthropic.RateLimitError (429)
│   └── anthropic.InternalServerError (500, 529)
├── anthropic.APIConnectionError（接続エラー）
└── anthropic.APITimeoutError（タイムアウト）
"""
    print(error_types)


def demonstrate_backoff_calculation() -> None:
    """
    Exponential backoff の計算例を表示する（APIなし）
    """
    print("\n--- Exponential Backoff の計算例 ---")
    print(f"設定: base_delay={BASE_DELAY}秒, max_delay={MAX_DELAY}秒, "
          f"backoff_factor={BACKOFF_FACTOR}")
    print()
    print(f"{'試行回数':<10} {'待機時間':<15} {'合計経過時間':<15}")
    print("-" * 40)

    total_elapsed = 0.0
    for attempt in range(MAX_RETRIES + 1):
        delay = calculate_backoff_delay(attempt)
        total_elapsed += delay
        print(f"{attempt + 1:<10} {delay:<15.1f} {total_elapsed:<15.1f}")

    print()
    print(f"最大リトライ後の合計待機時間: {total_elapsed:.1f}秒")


def demonstrate_error_handling(client: Anthropic) -> None:
    """
    実際のエラーハンドリングをデモする

    Args:
        client: Anthropicクライアント
    """
    print("\n--- エラーハンドリングのデモ ---")

    # 正常なリクエスト
    print("\n[正常なリクエスト]")
    messages = [{"role": "user", "content": "Pythonのリスト内包表記を1行で説明してください。"}]
    result = api_call_with_fallback(client, messages)
    print(f"応答: {result}")

    # 個別のエラータイプをキャッチする詳細な実装例
    print("\n[個別エラーハンドリングの実装例]")
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=100,
            messages=[{"role": "user", "content": "エラーハンドリングのテストです。"}]
        )
        print(f"✅ 成功: {response.content[0].text}")

    except anthropic.AuthenticationError as e:
        # 認証エラー: APIキーの問題
        logger.error(f"認証エラー（APIキーを確認してください）: {e}")
        print("❌ 認証エラー: APIキーが無効です")

    except anthropic.RateLimitError as e:
        # レート制限: 待機してリトライ
        logger.warning(f"レート制限エラー: {e}")
        print("⚠️  レート制限: しばらく待機してリトライが必要です")

    except anthropic.InternalServerError as e:
        # サーバーエラー: リトライ対象
        logger.error(f"サーバーエラー（{e.status_code}）: {e}")
        print(f"❌ サーバーエラー: ステータスコード {e.status_code}")

    except anthropic.APIConnectionError as e:
        # ネットワークエラー: 接続を確認
        logger.error(f"接続エラー: {e}")
        print("❌ 接続エラー: ネットワーク環境を確認してください")

    except anthropic.APIError as e:
        # その他のAPIエラー（基底クラスでキャッチ）
        logger.error(f"APIエラー: {e}")
        print(f"❌ APIエラー: {e}")


def error_handling_best_practices() -> None:
    """
    エラーハンドリングのベストプラクティスを表示する
    """
    print("\n--- エラーハンドリングのベストプラクティス ---")

    best_practices = """
【✅ エラーハンドリングのポイント】

1. エラーの種類に応じた適切な処理
   - 429/500/529: Exponential backoff でリトライ
   - 400/401/403: リトライせずに即座にエラーを通知
   - ネットワークエラー: リトライ（接続状態を確認）

2. Exponential Backoff の実装
   - 基本式: wait = base * (multiplier ^ attempt)
   - Jitter（ランダム揺らぎ）を加えることでスパイクを防ぐ
   - 最大待機時間を設定してリトライを制限する

3. タイムアウトの設定
   - 長時間のリクエストを防ぐ
   - ユーザー体験を損なわないよう適切な値を設定する（通常30〜60秒）

4. フォールバック戦略
   - APIが使えない場合のデフォルトレスポンスを用意する
   - キャッシュされた応答を返す
   - ユーザーに適切なエラーメッセージを表示する

5. 適切なロギング
   - エラーの詳細をログに記録する（PIIは除く）
   - リトライ回数と待機時間もログに残す
   - ログレベルを適切に設定する（ERROR, WARNING, INFO, DEBUG）

6. サーキットブレーカーパターン
   - 連続してエラーが発生する場合にAPIコールを一時停止
   - 一定時間後に再試行して回復を確認する

【⚠️ よくある間違い】

1. すべてのエラーをリトライ → 認証エラーはリトライしても無意味
2. リトライ回数を無制限に → コスト爆発、サービス悪化の原因
3. 待機なしの即座リトライ → レート制限をさらに悪化させる
4. エラーの握り潰し → デバッグ不能になる

【💡 CCA試験のポイント】
- anthropic.RateLimitError (429) は Exponential backoff でリトライ
- anthropic.InternalServerError には 500 と 529 (Overloaded) が含まれる
- エラーの継承関係を理解する（APIStatusError → RateLimitError など）
- retry-after ヘッダーがある場合はその値を使って待機する
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 60)
    print("エラーハンドリングとリトライロジック")
    print("=" * 60)

    # エラータイプの解説（APIなし）
    demonstrate_error_types()

    # Exponential Backoff の計算例（APIなし）
    demonstrate_backoff_calculation()

    # ベストプラクティスの表示（APIなし）
    error_handling_best_practices()

    # APIを使ったデモ
    print("\n--- API接続テスト ---")
    client = get_client()
    demonstrate_error_handling(client)

    print("\n✅ 完了！次は04_rate_limiting.pyに進んでください。")
