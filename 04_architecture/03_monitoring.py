"""
03_monitoring.py - モニタリングとロギング

このファイルの目的:
- Python logging モジュールを使ったログ実装を学ぶ
- 構造化ログ（JSON形式）の実装を習得する
- パフォーマンスメトリクスの収集方法を理解する
- エラートラッキングの実装を学ぶ
- トークン使用量のトラッキング方法を習得する

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 04_architecture/03_monitoring.py

【モニタリングが重要な理由】
本番環境では「何が起きているか」を常に把握する必要があります。
適切なモニタリングにより:
- パフォーマンスの問題を早期発見できる
- エラーの原因を迅速に特定できる
- コスト最適化のための情報が得られる
- SLA（サービスレベル合意）を達成・証明できる
"""

import json
import logging
import os
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
# 1. ログの設定
# =============================================================================

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    ロガーを設定する

    【ログレベルの意味】
    DEBUG   (10): 詳細なデバッグ情報（開発時のみ）
    INFO    (20): 通常の動作記録（処理開始・完了など）
    WARNING (30): 注意が必要な状況（リトライ、メモリ不足など）
    ERROR   (40): エラーが発生したが処理は継続（リクエスト失敗など）
    CRITICAL(50): 致命的なエラー（システム全体が停止）

    Args:
        log_level: ログレベル（logging.DEBUG/INFO/WARNING/ERROR/CRITICAL）
        log_file: ログファイルパス（Noneの場合はコンソールのみ）

    Returns:
        logging.Logger: 設定済みのロガー
    """
    # ロガーを取得（名前でロガーを識別する）
    logger = logging.getLogger("claude_monitor")
    logger.setLevel(log_level)

    # すでにハンドラが設定されている場合はスキップ（二重設定を防ぐ）
    if logger.handlers:
        return logger

    # フォーマッターの定義
    # %(asctime)s: 日時
    # %(name)s: ロガー名
    # %(levelname)s: ログレベル名
    # %(funcName)s: 関数名
    # %(message)s: ログメッセージ
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラ（標準出力）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ（オプション）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# グローバルロガーを設定
logger = setup_logging(log_level=logging.DEBUG)


# =============================================================================
# 2. 構造化ログの実装
# =============================================================================

class StructuredLogger:
    """
    構造化ログ（JSON形式）を出力するロガー

    通常のテキストログの代わりにJSON形式で出力することで:
    - ログ収集システム（Elasticsearch, CloudWatch等）での解析が容易
    - 特定フィールドでの絞り込みや集計が簡単
    - プログラムでの解析が容易

    Attributes:
        name: ロガー名
        base_logger: Python標準のロガー
    """

    def __init__(self, name: str):
        """
        Args:
            name: ロガー名（識別に使用）
        """
        self.name = name
        self.base_logger = logging.getLogger(name)

    def _log(self, level: int, event: str, **kwargs: Any) -> None:
        """
        構造化ログを出力する内部メソッド

        Args:
            level: ログレベル（logging.DEBUG等）
            event: イベント名（何が起きたかの識別子）
            **kwargs: 追加のコンテキスト情報
        """
        # 構造化ログのペイロードを構築
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logger": self.name,
            "event": event,
            **kwargs  # 追加のコンテキスト情報
        }

        # JSON文字列として出力
        log_message = json.dumps(log_data, ensure_ascii=False)
        self.base_logger.log(level, log_message)

    def debug(self, event: str, **kwargs: Any) -> None:
        """DEBUG レベルの構造化ログ"""
        self._log(logging.DEBUG, event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        """INFO レベルの構造化ログ"""
        self._log(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """WARNING レベルの構造化ログ"""
        self._log(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        """ERROR レベルの構造化ログ"""
        self._log(logging.ERROR, event, **kwargs)


# =============================================================================
# 3. パフォーマンスメトリクス収集
# =============================================================================

@dataclass
class RequestMetrics:
    """
    1回のAPIリクエストのメトリクス

    Attributes:
        request_id: リクエスト識別子
        prompt_preview: プロンプトの先頭40文字
        response_time: レスポンスタイム（秒）
        input_tokens: 入力トークン数
        output_tokens: 出力トークン数
        success: 成功したかどうか
        error_type: エラーの種類（エラー時のみ）
        timestamp: リクエスト送信時刻
    """
    request_id: int
    prompt_preview: str
    response_time: float
    input_tokens: int
    output_tokens: int
    success: bool
    error_type: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> int:
        """合計トークン数"""
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """
        概算コスト（USD）

        claude-sonnet-4 の概算料金:
        - 入力: $3.00 / 1M トークン
        - 出力: $15.00 / 1M トークン
        ※ 実際の料金は Anthropic の公式サイトで確認してください
        """
        input_cost = self.input_tokens * 3.00 / 1_000_000
        output_cost = self.output_tokens * 15.00 / 1_000_000
        return input_cost + output_cost


class MetricsCollector:
    """
    APIリクエストのメトリクスを収集・集計するクラス

    各リクエストのメトリクスを記録し、
    統計情報（平均、最大、最小など）を提供します。

    Attributes:
        metrics: 収集したメトリクスのリスト
        _request_counter: リクエストカウンター
    """

    def __init__(self):
        self.metrics: list[RequestMetrics] = []
        self._request_counter = 0
        self._error_counts: dict[str, int] = defaultdict(int)

    def record(
        self,
        prompt: str,
        response_time: float,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        error_type: Optional[str] = None
    ) -> RequestMetrics:
        """
        リクエストのメトリクスを記録する

        Args:
            prompt: プロンプト
            response_time: レスポンスタイム（秒）
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            success: 成功フラグ
            error_type: エラーの種類（エラー時のみ）

        Returns:
            RequestMetrics: 記録したメトリクス
        """
        self._request_counter += 1
        metrics = RequestMetrics(
            request_id=self._request_counter,
            prompt_preview=prompt[:40],
            response_time=response_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
            error_type=error_type
        )
        self.metrics.append(metrics)

        if error_type:
            self._error_counts[error_type] += 1

        return metrics

    @property
    def summary(self) -> dict:
        """メトリクスのサマリーを返す"""
        if not self.metrics:
            return {"message": "メトリクスなし"}

        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]
        response_times = [m.response_time for m in successful]
        total_input_tokens = sum(m.input_tokens for m in self.metrics)
        total_output_tokens = sum(m.output_tokens for m in self.metrics)
        total_cost = sum(m.estimated_cost_usd for m in self.metrics)

        return {
            "total_requests": len(self.metrics),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "error_rate": len(failed) / len(self.metrics) if self.metrics else 0.0,
            "response_time": {
                "min": min(response_times) if response_times else 0.0,
                "max": max(response_times) if response_times else 0.0,
                "avg": statistics.mean(response_times) if response_times else 0.0,
                "median": statistics.median(response_times) if response_times else 0.0,
                "p95": (
                    sorted(response_times)[int(len(response_times) * 0.95)]
                    if len(response_times) >= 20
                    else max(response_times, default=0.0)
                ),
            },
            "tokens": {
                "total_input": total_input_tokens,
                "total_output": total_output_tokens,
                "total": total_input_tokens + total_output_tokens,
            },
            "cost": {
                "total_usd": total_cost,
                "avg_per_request_usd": total_cost / len(self.metrics),
            },
            "error_breakdown": dict(self._error_counts),
        }

    def print_summary(self) -> None:
        """メトリクスのサマリーを見やすく表示する"""
        s = self.summary
        print("\n" + "=" * 50)
        print("📊 メトリクスサマリー")
        print("=" * 50)
        print(f"総リクエスト数: {s['total_requests']}")
        print(f"  ✅ 成功: {s['successful_requests']}")
        print(f"  ❌ 失敗: {s['failed_requests']}")
        print(f"  エラー率: {s['error_rate'] * 100:.1f}%")
        print()
        rt = s['response_time']
        print("レスポンスタイム:")
        print(f"  最小: {rt['min']:.3f}秒")
        print(f"  最大: {rt['max']:.3f}秒")
        print(f"  平均: {rt['avg']:.3f}秒")
        print(f"  中央値: {rt['median']:.3f}秒")
        print()
        t = s['tokens']
        print("トークン使用量:")
        print(f"  入力: {t['total_input']:,} トークン")
        print(f"  出力: {t['total_output']:,} トークン")
        print(f"  合計: {t['total']:,} トークン")
        print()
        c = s['cost']
        print("概算コスト:")
        print(f"  合計: ${c['total_usd']:.6f}")
        print(f"  1リクエスト平均: ${c['avg_per_request_usd']:.6f}")
        if s['error_breakdown']:
            print()
            print("エラー内訳:")
            for error_type, count in s['error_breakdown'].items():
                print(f"  {error_type}: {count}件")
        print("=" * 50)


# =============================================================================
# 4. モニタリング付きAPIクライアント
# =============================================================================

class MonitoredAPIClient:
    """
    モニタリング機能を持つAPIクライアント

    すべてのAPIリクエストを自動的に計測・記録します。

    Attributes:
        client: Anthropicクライアント
        metrics: メトリクスコレクター
        structured_logger: 構造化ロガー
        alert_thresholds: アラートの閾値
    """

    def __init__(
        self,
        response_time_threshold: float = 10.0,
        error_rate_threshold: float = 0.1
    ):
        """
        Args:
            response_time_threshold: アラートを発生させるレスポンスタイム（秒）
            error_rate_threshold: アラートを発生させるエラー率（0.0〜1.0）
        """
        self.client = get_client()
        self.metrics = MetricsCollector()
        self.structured_logger = StructuredLogger("claude_api")
        self.response_time_threshold = response_time_threshold
        self.error_rate_threshold = error_rate_threshold

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 512
    ) -> Optional[str]:
        """
        モニタリング付きAPIクエリ

        リクエストの計測、ログ出力、アラートチェックを自動実行します。

        Args:
            prompt: ユーザーのプロンプト
            system: システムプロンプト（オプション）
            max_tokens: 最大トークン数

        Returns:
            Optional[str]: レスポンステキスト、エラー時はNone
        """
        # リクエスト開始のログ
        self.structured_logger.info(
            "api_request_start",
            prompt_preview=prompt[:40],
            max_tokens=max_tokens
        )

        start = time.time()
        try:
            params: dict[str, Any] = {
                "model": MODEL_NAME,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system:
                params["system"] = system

            response = self.client.messages.create(**params)
            elapsed = time.time() - start

            # メトリクスを記録
            m = self.metrics.record(
                prompt=prompt,
                response_time=elapsed,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                success=True
            )

            # 成功ログ（構造化）
            self.structured_logger.info(
                "api_request_success",
                request_id=m.request_id,
                response_time=elapsed,
                input_tokens=m.input_tokens,
                output_tokens=m.output_tokens,
                cost_usd=m.estimated_cost_usd
            )

            # レスポンスタイムのアラートチェック
            if elapsed > self.response_time_threshold:
                self.structured_logger.warning(
                    "slow_response_alert",
                    response_time=elapsed,
                    threshold=self.response_time_threshold,
                    message=f"レスポンスタイムが閾値を超えました: {elapsed:.3f}秒 > {self.response_time_threshold}秒"
                )

            return response.content[0].text

        except Exception as e:
            elapsed = time.time() - start
            error_type = type(e).__name__

            # エラーメトリクスを記録
            self.metrics.record(
                prompt=prompt,
                response_time=elapsed,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error_type=error_type
            )

            # エラーログ（構造化）
            self.structured_logger.error(
                "api_request_failed",
                error_type=error_type,
                error_message=str(e),
                response_time=elapsed
            )

            # エラー率のアラートチェック
            summary = self.metrics.summary
            if summary.get("error_rate", 0) > self.error_rate_threshold:
                self.structured_logger.warning(
                    "high_error_rate_alert",
                    current_error_rate=summary["error_rate"],
                    threshold=self.error_rate_threshold,
                    message=f"エラー率が閾値を超えました: {summary['error_rate'] * 100:.1f}%"
                )

            return None


# =============================================================================
# 5. デモ関数
# =============================================================================

def demonstrate_logging_levels() -> None:
    """
    ログレベルのデモ（APIなし）
    """
    print("\n--- 1. ログレベルのデモ ---")
    demo_logger = setup_logging(log_level=logging.DEBUG)

    demo_logger.debug("DEBUG: 詳細なデバッグ情報（開発時のみ表示）")
    demo_logger.info("INFO: 通常の動作記録（リクエスト処理開始など）")
    demo_logger.warning("WARNING: 注意が必要な状況（レート制限に近づいているなど）")
    demo_logger.error("ERROR: エラーが発生（APIコール失敗など）")
    demo_logger.critical("CRITICAL: 致命的なエラー（システム全体の停止）")


def demonstrate_structured_logging() -> None:
    """
    構造化ログのデモ（APIなし）
    """
    print("\n--- 2. 構造化ログ（JSON形式）のデモ ---")
    sl = StructuredLogger("demo")

    sl.info(
        "api_request",
        request_id=1,
        prompt="Pythonとは？",
        model=MODEL_NAME,
        max_tokens=100
    )
    sl.info(
        "api_success",
        request_id=1,
        response_time=1.23,
        input_tokens=15,
        output_tokens=45
    )
    sl.warning(
        "rate_limit_warning",
        current_rpm=58,
        limit_rpm=60,
        message="レート制限に近づいています"
    )
    sl.error(
        "api_error",
        error_type="RateLimitError",
        status_code=429,
        retry_after=30
    )


def demonstrate_monitoring(client: MonitoredAPIClient) -> None:
    """
    モニタリング付きクライアントのデモ

    Args:
        client: モニタリング付きAPIクライアント
    """
    print("\n--- 3. モニタリング付きAPIクライアントのデモ ---")

    test_prompts = [
        "Pythonのリスト内包表記を1文で説明してください。",
        "Javaの特徴を1文で説明してください。",
        "データベースのインデックスを1文で説明してください。",
    ]

    for prompt in test_prompts:
        result = client.query(prompt, max_tokens=100)
        if result:
            print(f"✅ {prompt[:30]}... → {result[:50]}...")
        else:
            print(f"❌ {prompt[:30]}... → エラー")
        time.sleep(0.5)  # レート制限対策


def monitoring_best_practices() -> None:
    """モニタリングのベストプラクティスを表示する"""
    print("\n--- モニタリングのベストプラクティス ---")

    best_practices = """
【✅ モニタリングのポイント】

1. ログレベルの使い分け
   - DEBUG: 開発・デバッグ時のみ（本番では無効化）
   - INFO: 通常の処理記録（リクエスト開始・完了）
   - WARNING: 注意が必要だが処理は継続（リトライなど）
   - ERROR: エラーが発生（APIコール失敗など）
   - CRITICAL: システム全体に影響するエラー

2. 構造化ログのメリット
   - JSON形式で機械可読なログを出力
   - ログ収集システムでの検索・集計が容易
   - "event"フィールドでイベントの種類を識別

3. 重要なメトリクス
   - レスポンスタイム（平均、P95、P99）
   - エラー率（エラー数 / 総リクエスト数）
   - トークン使用量（コスト管理）
   - スループット（単位時間あたりのリクエスト数）

4. アラートの設定
   - レスポンスタイムが閾値を超えた場合
   - エラー率が閾値を超えた場合
   - トークン使用量が予算を超えた場合

5. ログファイルの管理
   - RotatingFileHandler でログファイルのサイズを制限
   - 定期的なアーカイブと削除
   - 機密情報（APIキー、PII）はログに含めない

【💡 CCA試験のポイント】
- Python logging の基本（basicConfig, getLogger, setLevel）
- ログレベル: DEBUG < INFO < WARNING < ERROR < CRITICAL
- 構造化ログ = JSON形式のログ（機械可読）
- メトリクス収集 = パフォーマンス測定・コスト管理の基盤
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 60)
    print("モニタリングとロギング")
    print("=" * 60)

    # 1. ログレベルのデモ（APIなし）
    demonstrate_logging_levels()

    # 2. 構造化ログのデモ（APIなし）
    demonstrate_structured_logging()

    # 3. モニタリング付きクライアントのデモ
    print("\n--- API接続テスト ---")
    monitored_client = MonitoredAPIClient(
        response_time_threshold=10.0,
        error_rate_threshold=0.5
    )
    demonstrate_monitoring(monitored_client)

    # メトリクスサマリーを表示
    monitored_client.metrics.print_summary()

    # ベストプラクティス表示
    monitoring_best_practices()

    print("\n✅ 完了！次は04_scalable_design.pyに進んでください。")
