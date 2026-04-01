"""
exercise_02.py - 練習問題2: リトライ機能付きAPIクライアント

難易度: ⭐⭐⭐ 中上級
目的: 堅牢なエラーハンドリングとリトライロジックを持つAPIクライアントを実装する

【課題】
以下の機能を持つRobustAPIClientクラスを完成させてください:
1. Exponential backoff でのリトライ（最大3回）
2. 複数のエラータイプへの個別対応
3. タイムアウト処理（30秒）
4. ロギング機能（INFO, WARNING, ERROR レベルを適切に使用）
5. レート制限の遵守（簡易的なリクエスト間隔の制御）

【期待される出力】
============================================================
リトライ機能付きAPIクライアント
============================================================
2026-01-01 10:00:00,000 - INFO - リクエスト送信: 'Pythonとは何ですか？'
2026-01-01 10:00:01,234 - INFO - ✅ 成功 (入力: 15トークン, 出力: 52トークン)
応答: Pythonはシンプルな文法...

2026-01-01 10:00:01,235 - INFO - リクエスト送信: '機械学習とは？'
2026-01-01 10:00:02,456 - INFO - ✅ 成功 (入力: 10トークン, 出力: 45トークン)
応答: 機械学習とは...

--- 統計 ---
総リクエスト: 2, 成功: 2, 失敗: 0, リトライ: 0
平均応答時間: 1.2秒

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
"""

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic
from anthropic import Anthropic

# 使用するモデル名
MODEL_NAME = "claude-sonnet-4-20250514"

# リトライの設定
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 30.0
REQUEST_TIMEOUT_SECONDS = 30
MIN_REQUEST_INTERVAL = 0.5  # リクエスト間の最小間隔（秒）

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
class RequestStats:
    """リクエストの統計情報"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_retries: int = 0
    total_response_time: float = 0.0
    start_time: float = field(default_factory=time.time)

    @property
    def average_response_time(self) -> float:
        """平均応答時間（秒）"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests

    def summary(self) -> str:
        """統計サマリーを返す"""
        return (
            f"統計:\n"
            f"  総リクエスト: {self.total_requests}\n"
            f"  成功: {self.successful_requests}\n"
            f"  失敗: {self.failed_requests}\n"
            f"  リトライ: {self.total_retries}\n"
            f"  平均応答時間: {self.average_response_time:.2f}秒"
        )


def calculate_backoff_delay(attempt: int) -> float:
    """
    Exponential backoff の待機時間を計算する

    Args:
        attempt: 現在の試行回数（0から始まる）

    Returns:
        float: 待機時間（秒）

    TODO: 以下を実装してください
    - 計算式: min(BASE_DELAY_SECONDS * (2 ** attempt), MAX_DELAY_SECONDS)
    - 例: attempt=0 → 1.0秒, attempt=1 → 2.0秒, attempt=2 → 4.0秒

    ヒント:
    - min() 関数で上限を設定する
    - ** 演算子でべき乗を計算する
    """
    # TODO: ここに実装してください
    pass


class RobustAPIClient:
    """
    堅牢なエラーハンドリングとリトライ機能を持つAPIクライアント

    TODO: このクラスの以下のメソッドを実装してください:
    1. _wait_for_rate_limit(): リクエスト間隔を制御する
    2. _make_request_with_retry(): リトライ付きAPIリクエスト
    3. chat(): 高レベルのチャット関数
    """

    def __init__(self, client: Anthropic) -> None:
        """
        クライアントを初期化する

        Args:
            client: Anthropicクライアント
        """
        self.client = client
        self.stats = RequestStats()
        self._last_request_time: float = 0.0

    def _wait_for_rate_limit(self) -> None:
        """
        レート制限のためにリクエスト間隔を確保する

        TODO: 以下を実装してください
        1. 前回のリクエスト時刻からの経過時間を計算する
        2. MIN_REQUEST_INTERVAL に満たない場合は sleep する
        3. 現在時刻を _last_request_time に記録する

        ヒント:
        - time.time() で現在時刻を取得
        - elapsed = time.time() - self._last_request_time
        - wait_time = MIN_REQUEST_INTERVAL - elapsed
        - if wait_time > 0: time.sleep(wait_time)
        """
        # TODO: ここに実装してください
        pass

    def _make_request_with_retry(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 512
    ) -> Optional[dict]:
        """
        リトライ付きでAPIリクエストを行う

        Args:
            messages: メッセージリスト
            system: システムプロンプト
            max_tokens: 最大出力トークン数

        Returns:
            Optional[dict]: {
                "text": str,           # 応答テキスト
                "input_tokens": int,   # 入力トークン数
                "output_tokens": int,  # 出力トークン数
                "retries": int         # リトライ回数
            } または None（失敗時）

        TODO: 以下を実装してください
        1. MAX_RETRIES 回まで以下をループ:
           a. _wait_for_rate_limit() を呼び出す
           b. API リクエストを送信する
           c. 成功した場合は結果を返す
           d. RateLimitError (429) の場合:
              - WARNING ログ: "429 レート制限。X秒後にリトライ（Y/3回目）"
              - calculate_backoff_delay(attempt) 秒待機
              - stats.total_retries をインクリメント
           e. InternalServerError (500/529) の場合:
              - WARNING ログ: "サーバーエラー。リトライ..."
              - 同様にバックオフして待機
           f. その他の APIStatusError:
              - ERROR ログ: "リトライ不可能なエラー: ..."
              - すぐに None を返す（リトライしない）
           g. APIConnectionError / APITimeoutError:
              - WARNING ログ: "接続エラー。リトライ..."
              - バックオフして待機
        2. 最大リトライ回数を超えた場合は None を返す

        ヒント:
        - for attempt in range(MAX_RETRIES + 1): でループ
        - try-except で各エラータイプをキャッチ
        - anthropic.RateLimitError, anthropic.InternalServerError などを使う
        - logger.warning(), logger.error() でログを記録
        """
        # TODO: ここに実装してください
        pass

    def chat(self, message: str, system: Optional[str] = None) -> Optional[str]:
        """
        シンプルなチャット関数

        Args:
            message: ユーザーメッセージ
            system: システムプロンプト

        Returns:
            Optional[str]: 応答テキスト、または None（失敗時）

        TODO: 以下を実装してください
        1. stats.total_requests をインクリメント
        2. 開始時刻を記録する
        3. logger.info() でリクエストをログに記録
        4. _make_request_with_retry() を呼び出す
        5. 成功時:
           - stats.successful_requests をインクリメント
           - stats.total_response_time に応答時間を加算
           - logger.info() で成功をログに記録（トークン数も含める）
           - 応答テキストを返す
        6. 失敗時:
           - stats.failed_requests をインクリメント
           - logger.error() で失敗をログに記録
           - None を返す

        ヒント:
        - start_time = time.time()
        - elapsed = time.time() - start_time
        - result = self._make_request_with_retry(...)
        - if result is not None: ...
        """
        # TODO: ここに実装してください
        pass


def run_demo(client: Anthropic) -> None:
    """
    デモを実行する

    Args:
        client: Anthropicクライアント
    """
    print("=" * 60)
    print("リトライ機能付きAPIクライアント")
    print("=" * 60)

    # RobustAPIClientを使う
    robust_client = RobustAPIClient(client)

    # 複数のリクエストを送信
    questions = [
        "Pythonとは何ですか？一文で答えてください。",
        "機械学習とは何ですか？一文で答えてください。",
        "APIとは何ですか？一文で答えてください。",
        "クラウドコンピューティングとは？一文で答えてください。",
        "セキュリティとは何ですか？一文で答えてください。",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n--- リクエスト {i} ---")
        response = robust_client.chat(question)
        if response:
            print(f"応答: {response}")
        else:
            print("❌ 応答を取得できませんでした")

    # 統計を表示
    print(f"\n{robust_client.stats.summary()}")


if __name__ == "__main__":
    client = get_client()
    run_demo(client)
