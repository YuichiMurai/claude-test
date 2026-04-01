"""
exercise_02.py - 練習問題2: モニタリングシステムの実装

難易度: ⭐⭐⭐⭐ 上級

目的:
包括的なモニタリングとロギングシステムを構築する。

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行

【実装する機能】
1. 構造化ログ（JSON形式）
2. メトリクス収集（レスポンスタイム、トークン使用量、エラー率）
3. アラート機能（閾値超過時に警告）
4. ダッシュボード表示
5. 異常検知（標準偏差ベース）

【参考ファイル】
- 04_architecture/03_monitoring.py - モニタリング実装
"""

import json  # noqa: F401 - students will use json.dumps() in TODO 1-1 (_build_log_data method)
import logging
import os
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone  # noqa: F401 - students will use these in their implementation
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
# TODO 1: 構造化ロガーを実装する
# =============================================================================

class MonitoringLogger:
    """
    JSON形式の構造化ログを出力するロガー

    【ヒント】
    - logging.getLogger(name) でロガーを取得する
    - json.dumps() でdictをJSON文字列に変換する
    - 各ログにタイムスタンプ、ロガー名、イベント名を含める
    """

    def __init__(self, name: str, log_level: int = logging.INFO):
        """
        Args:
            name: ロガー名
            log_level: ログレベル
        """
        self.name = name
        # Python標準のロガーを設定する
        self._logger = logging.getLogger(name)
        self._logger.setLevel(log_level)

        # ハンドラが未設定の場合のみ追加（二重設定防止）
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def _build_log_data(self, event: str, **kwargs: Any) -> str:
        """
        TODO 1-1: JSON形式のログデータを構築する

        以下のフィールドを含む dict を作成して JSON 文字列で返す:
        - "timestamp": datetime.now(timezone.utc).isoformat()
        - "logger": self.name
        - "event": event
        - その他: **kwargs の内容をすべて含める

        Args:
            event: イベント名
            **kwargs: 追加のコンテキスト情報

        Returns:
            str: JSON文字列
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def info(self, event: str, **kwargs: Any) -> None:
        """INFO レベルのログを出力する"""
        # TODO 1-2: _build_log_data でJSON文字列を作成して self._logger.info() で出力する
        pass  # 削除してください

    def warning(self, event: str, **kwargs: Any) -> None:
        """WARNING レベルのログを出力する"""
        # TODO 1-3: _build_log_data でJSON文字列を作成して self._logger.warning() で出力する
        pass  # 削除してください

    def error(self, event: str, **kwargs: Any) -> None:
        """ERROR レベルのログを出力する"""
        # TODO 1-4: _build_log_data でJSON文字列を作成して self._logger.error() で出力する
        pass  # 削除してください


# =============================================================================
# TODO 2: メトリクス収集クラスを実装する
# =============================================================================

@dataclass
class RequestRecord:
    """
    1回のリクエストの記録

    Attributes:
        prompt_preview: プロンプト先頭40文字
        response_time: レスポンスタイム（秒）
        input_tokens: 入力トークン数
        output_tokens: 出力トークン数
        success: 成功フラグ
        error_type: エラーの種類（エラー時のみ）
        timestamp: 記録時刻
    """
    prompt_preview: str
    response_time: float
    input_tokens: int
    output_tokens: int
    success: bool
    error_type: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    @property
    def estimated_cost_usd(self) -> float:
        """概算コスト（USD）"""
        # 入力: $3.00/1M、出力: $15.00/1M（概算）
        return (self.input_tokens * 3.00 + self.output_tokens * 15.00) / 1_000_000


class AdvancedMetricsCollector:
    """
    高度なメトリクス収集クラス

    パフォーマンスメトリクスの収集に加えて、
    アラートと異常検知を実装する。
    """

    def __init__(
        self,
        response_time_alert_threshold: float = 5.0,
        error_rate_alert_threshold: float = 0.1
    ):
        """
        Args:
            response_time_alert_threshold: アラートを発生させるレスポンスタイム（秒）
            error_rate_alert_threshold: アラートを発生させるエラー率（0.0〜1.0）
        """
        self.records: list[RequestRecord] = []
        self.response_time_threshold = response_time_alert_threshold
        self.error_rate_threshold = error_rate_alert_threshold
        self.alerts: list[str] = []

    def record(
        self,
        prompt: str,
        response_time: float,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        error_type: Optional[str] = None
    ) -> RequestRecord:
        """
        TODO 2-1: リクエストを記録してアラートをチェックする

        手順:
        1. RequestRecord を作成して self.records に追加する
        2. check_alerts() を呼び出してアラートをチェックする
        3. 作成した RequestRecord を返す

        Args:
            prompt: プロンプト
            response_time: レスポンスタイム（秒）
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            success: 成功フラグ
            error_type: エラーの種類

        Returns:
            RequestRecord: 記録したデータ
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def check_alerts(self, record: RequestRecord) -> None:
        """
        TODO 2-2: アラートをチェックして alerts リストに追加する

        以下の条件でアラートを生成する:
        1. レスポンスタイムが response_time_threshold を超えた場合:
           f"⚠️  ALERT: レスポンスタイムが閾値を超えました（{record.response_time:.1f}秒 > {self.response_time_threshold}秒）"
        2. エラー率（失敗数/総数）が error_rate_threshold を超えた場合:
           f"⚠️  ALERT: エラー率が閾値を超えました（{error_rate * 100:.1f}% > {self.error_rate_threshold * 100:.1f}%）"

        アラートメッセージを print() して self.alerts に追加する

        Args:
            record: チェックするリクエスト記録
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def detect_anomalies(self) -> list[dict]:
        """
        TODO 2-3: 異常なレスポンスタイムを検出する

        異常検知の方法:
        - 成功したリクエストのレスポンスタイムを収集する
        - 平均（mean）と標準偏差（stdev）を計算する
        - 平均 + 2 × 標準偏差 を超えるレスポンスタイムを「異常」とする
        - データが3件未満の場合は空リストを返す

        【統計の知識】
        正規分布では、平均 ± 2σ の範囲に約95%のデータが含まれる。
        それを超える値は「外れ値（異常値）」として検出できる。

        Returns:
            list[dict]: 異常検知した記録のリスト（各要素は dict 形式）
                [{"prompt": ..., "response_time": ..., "threshold": ...}, ...]
        """
        successful = [r for r in self.records if r.success]
        if len(successful) < 3:
            return []

        # TODO: statistics.mean() と statistics.stdev() を使って実装してください
        pass  # 削除してください

    @property
    def summary(self) -> dict:
        """メトリクスサマリーを返す"""
        if not self.records:
            return {"message": "データなし"}

        successful = [r for r in self.records if r.success]
        failed = [r for r in self.records if not r.success]
        rt = [r.response_time for r in successful]
        total_tokens = sum(r.input_tokens + r.output_tokens for r in self.records)
        total_cost = sum(r.estimated_cost_usd for r in self.records)

        return {
            "total": len(self.records),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.records),
            "response_time_avg": statistics.mean(rt) if rt else 0.0,
            "response_time_p95": (
                sorted(rt)[int(len(rt) * 0.95)]
                if len(rt) >= 20
                else max(rt, default=0.0)
            ),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "alert_count": len(self.alerts),
        }


# =============================================================================
# TODO 3: モニタリング付きAPIクライアントを完成させる
# =============================================================================

class MonitoringSystemClient:
    """
    モニタリングシステムを統合したAPIクライアント
    """

    def __init__(
        self,
        response_time_threshold: float = 5.0,
        error_rate_threshold: float = 0.1
    ):
        self.client = get_client()
        self.logger = MonitoringLogger("claude_monitor")
        self.metrics = AdvancedMetricsCollector(
            response_time_alert_threshold=response_time_threshold,
            error_rate_alert_threshold=error_rate_threshold
        )

    def query(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """
        TODO 3: モニタリング付きAPIクエリを実装する

        手順:
        1. self.logger.info("api_request_start", ...) でリクエスト開始をログ
        2. time.time() でタイマー開始
        3. self.client.messages.create(...) でAPIを呼び出す
        4. 成功時: self.metrics.record(...) でメトリクス記録
        5. 成功時: self.logger.info("api_request_success", ...) でログ
        6. エラー時: self.metrics.record(..., success=False) でメトリクス記録
        7. エラー時: self.logger.error("api_request_failed", ...) でログ
        8. 成功したらレスポンステキストを、エラー時は None を返す

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            Optional[str]: レスポンステキスト
        """
        # TODO: ここを実装してください
        pass  # 削除してください

    def print_dashboard(self) -> None:
        """ダッシュボードを表示する"""
        s = self.summary
        anomalies = self.metrics.detect_anomalies()

        print("\n" + "=" * 50)
        print("📊 ダッシュボード")
        print("=" * 50)
        print(f"総リクエスト数: {s.get('total', 0)}")
        print(f"成功率: {s.get('success_rate', 0) * 100:.1f}%")
        print(f"平均レスポンスタイム: {s.get('response_time_avg', 0):.3f}秒")
        print(f"P95レスポンスタイム: {s.get('response_time_p95', 0):.3f}秒")
        print(f"合計トークン: {s.get('total_tokens', 0):,}")
        print(f"概算コスト: ${s.get('total_cost_usd', 0):.6f}")
        print(f"アラート数: {s.get('alert_count', 0)}")
        if anomalies:
            print(f"異常検知: {len(anomalies)}件")
            for a in anomalies:
                print(f"  ⚠️  {a.get('prompt', '')[:30]}... "
                      f"({a.get('response_time', 0):.2f}秒 > 閾値{a.get('threshold', 0):.2f}秒)")
        print("=" * 50)

    @property
    def summary(self) -> dict:
        """メトリクスサマリー"""
        return self.metrics.summary


# =============================================================================
# メイン関数
# =============================================================================

def main() -> None:
    """モニタリングシステムのデモ"""
    print("=" * 60)
    print("練習問題2: モニタリングシステム")
    print("=" * 60)

    monitoring_client = MonitoringSystemClient(
        response_time_threshold=10.0,
        error_rate_threshold=0.5
    )

    # テスト用プロンプト
    test_prompts = [
        "Pythonの特徴を1文で教えてください。",
        "機械学習とは何ですか？1文で。",
        "クラウドコンピューティングとは？1文で。",
        "APIとは何ですか？1文で。",
        "データベースのインデックスとは？1文で。",
    ]

    print("\n[APIリクエストの実行]")
    for prompt in test_prompts:
        result = monitoring_client.query(prompt, max_tokens=100)
        if result:
            print(f"✅ {prompt[:30]}... → {result[:40]}...")
        else:
            print(f"❌ {prompt[:30]}... → エラー")
        time.sleep(0.3)  # レート制限対策

    # ダッシュボード表示
    monitoring_client.print_dashboard()

    print("\n✅ 完了！次はexercise_03.pyに進んでください。")


if __name__ == "__main__":
    main()
