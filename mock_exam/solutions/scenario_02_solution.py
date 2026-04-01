"""
scenario_02_solution.py - ドキュメント要約システム（模範解答）

【このファイルの目的】
シナリオ2「ドキュメント要約システム」の模範解答です。
すべての要件を満たした最高品質のコードを示します。

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定（Colab Secretsに設定済みの場合は不要）:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行

【学習のポイント】
- 長文処理の鍵は「適切なチャンク分割」。分割単位（段落→文）を段階的に試みる
- 階層的要約は「ボトムアップ」の考え方: 部分→全体の順で要約する
- キーポイント抽出はClaudeに番号付きリストで返答させると解析が簡単
- 品質評価は定量指標（長さ比率・キーワード包含率）で自動化できる

【CCA試験でのポイント】
- トークン管理: 日本語は1トークン ≈ 0.5文字が目安（概算）
- 階層的処理は「Map-Reduce」パターン — 分散処理の基本設計
- 品質評価を自動化することで人間のレビューコストを削減できる
- 複数形式対応はファクトリパターンで拡張性を持たせるとよい
"""

import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic
from anthropic import Anthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"

# チャンク分割のパラメータ
# 日本語は1トークン ≈ 0.5文字が目安（概算）
MAX_CHUNK_CHARS = 1000      # 最大チャンクサイズ（文字数）
TARGET_SUMMARY_RATIO_MIN = 0.20   # 要約の目標長さ比率（下限）
TARGET_SUMMARY_RATIO_MAX = 0.30   # 要約の目標長さ比率（上限）
QUALITY_THRESHOLD = 0.6           # 品質スコアの合格閾値

# リトライパラメータ
MAX_RETRIES = 3
BASE_DELAY = 1.0


def get_client() -> Anthropic:
    """APIクライアントを取得"""
    try:
        from google.colab import userdata
        api_key = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')

    return Anthropic(api_key=api_key)


@dataclass
class SummaryResult:
    """要約結果を保持するデータクラス"""

    original_text: str
    format_type: str          # "plaintext" / "markdown" / "structured"
    chunk_count: int
    chunk_summaries: list[str]
    final_summary: str
    key_points: list[str]
    quality_score: float
    quality_details: dict = field(default_factory=dict)


def detect_format(text: str) -> str:
    """
    テキストの形式を自動判定する

    CCA試験のポイント:
    - 正規表現で形式を判定するシンプルなアプローチ
    - 判定ロジックを関数に分離することで単体テストが可能

    Args:
        text: 判定対象のテキスト

    Returns:
        str: "markdown" / "structured" / "plaintext"
    """
    # マークダウン: #見出し または **強調** が含まれる
    if re.search(r'^#{1,6}\s', text, re.MULTILINE) or '**' in text or '__' in text:
        return "markdown"

    # 構造化テキスト: 「第N章」「N.」「・」などの構造的な記号が含まれる
    if re.search(r'(第\d+[章節]|^\d+\.|^[\・•])', text, re.MULTILINE):
        return "structured"

    return "plaintext"


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """
    テキストをトークン制限を考慮してチャンクに分割する

    分割戦略（優先順位）:
    1. 段落単位（\n\n）で分割を試みる
    2. 段落が大きすぎる場合は文章単位（。\n）で分割する
    3. それでも大きすぎる場合は文字数で強制分割する

    CCA試験のポイント:
    - 意味のある単位での分割が要約精度を高める
    - チャンクサイズが小さすぎると文脈が失われる
    - チャンクサイズが大きすぎるとトークン制限を超える

    Args:
        text: 分割対象のテキスト
        max_chars: 最大チャンクサイズ（文字数）

    Returns:
        list[str]: 分割されたチャンクのリスト
    """
    # 段落（\n\n区切り）に分割
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # 段落を追加してもmax_charsを超えない場合
        if len(current_chunk) + len(paragraph) + 2 <= max_chars:
            current_chunk += (paragraph + "\n\n") if current_chunk else paragraph
        else:
            # 現在のチャンクを確定
            if current_chunk:
                chunks.append(current_chunk.strip())

            # 段落自体がmax_charsを超える場合は文章単位で分割
            if len(paragraph) > max_chars:
                # 句点（。）または改行で文章を分割
                sentences = re.split(r'(?<=。)|(?<=\n)', paragraph)
                sub_chunk = ""
                for sentence in sentences:
                    if len(sub_chunk) + len(sentence) <= max_chars:
                        sub_chunk += sentence
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        # それでも長すぎる場合は文字数で強制分割
                        if len(sentence) > max_chars:
                            for i in range(0, len(sentence), max_chars):
                                chunks.append(sentence[i:i + max_chars].strip())
                        else:
                            sub_chunk = sentence
                if sub_chunk:
                    chunks.append(sub_chunk.strip())
                current_chunk = ""
            else:
                current_chunk = paragraph

    # 残ったチャンクを追加
    if current_chunk:
        chunks.append(current_chunk.strip())

    print(f"📦 チャンク分割完了: {len(chunks)}個 (最大{max_chars}文字/チャンク)")
    for i, chunk in enumerate(chunks):
        print(f"  チャンク{i + 1}: {len(chunk)}文字")

    return chunks


def _call_with_retry(client: Anthropic, **kwargs) -> str:
    """
    リトライロジック付きでAPIを呼び出す

    Exponential backoff でリトライする。
    RateLimitError と APIStatusError のみリトライ対象とする。

    Args:
        client: Anthropic クライアント
        **kwargs: messages.create() に渡す引数

    Returns:
        str: APIのレスポンステキスト

    Raises:
        anthropic.APIError: リトライ上限を超えた場合
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(**kwargs)
            return response.content[0].text

        except anthropic.RateLimitError as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"⚠️ レート制限 (試行{attempt + 1}/{MAX_RETRIES})。{wait_time}秒後にリトライ...")
                time.sleep(wait_time)
            else:
                raise e

        except anthropic.APIStatusError as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"⚠️ APIエラー {e.status_code} (試行{attempt + 1}/{MAX_RETRIES})。{wait_time}秒後にリトライ...")
                time.sleep(wait_time)
            else:
                raise e

    # ここには到達しないが型チェックのため
    raise RuntimeError("リトライ上限を超えました")


def summarize_chunk(client: Anthropic, chunk: str, chunk_index: int) -> str:
    """
    テキストの1チャンクを要約する

    CCA試験のポイント:
    - チャンク要約のプロンプトは簡潔に（余分なトークンを節約）
    - 「元のテキストの約30%の長さ」と明示することで長さを制御できる

    Args:
        client: Anthropic クライアント
        chunk: 要約対象のチャンク
        chunk_index: チャンクのインデックス（ログ用）

    Returns:
        str: チャンクの要約テキスト
    """
    print(f"  📝 チャンク{chunk_index + 1}を要約中...")

    summary = _call_with_retry(
        client,
        model=MODEL_NAME,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下のテキストを元の30%程度の長さに要約してください。"
                    f"重要な情報・数値・固有名詞を保持してください。\n\n"
                    f"テキスト:\n{chunk}"
                ),
            }
        ],
    )

    return summary


def hierarchical_summarize(client: Anthropic, chunk_summaries: list[str]) -> str:
    """
    チャンク要約を統合して全体要約を生成する（階層的要約）

    CCA試験のポイント:
    - Map-Reduceパターン: chunk_summaries（Map段階）を統合（Reduce段階）
    - チャンク要約の連結が長い場合は再帰的に適用することもできる
    - 全体要約では「このドキュメントは〇〇について述べています」の形式が読みやすい

    Args:
        client: Anthropic クライアント
        chunk_summaries: 各チャンクの要約リスト

    Returns:
        str: ドキュメント全体の要約テキスト
    """
    print("📊 全体要約を生成中...")

    # チャンク要約を番号付きで連結
    combined_summaries = "\n\n".join(
        f"【パート{i + 1}】{summary}"
        for i, summary in enumerate(chunk_summaries)
    )

    final_summary = _call_with_retry(
        client,
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下は長文ドキュメントを分割して要約したものです。"
                    f"これらを統合して、ドキュメント全体の一貫した要約を作成してください。"
                    f"元のドキュメントの20〜30%程度の長さを目標にしてください。\n\n"
                    f"{combined_summaries}"
                ),
            }
        ],
    )

    return final_summary


def extract_key_points(client: Anthropic, text: str) -> list[str]:
    """
    テキストから重要なキーポイントを抽出する

    3〜5個のキーポイントを番号付きリストで返す。

    CCA試験のポイント:
    - 「番号付きリスト形式のみ」と指示することで解析が簡単になる
    - キーポイント数の上下限を明示することで過不足を防ぐ

    Args:
        client: Anthropic クライアント
        text: キーポイントを抽出する元テキスト

    Returns:
        list[str]: キーポイントのリスト（3〜5個）
    """
    print("🔑 キーポイントを抽出中...")

    response = _call_with_retry(
        client,
        model=MODEL_NAME,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下のテキストから最重要ポイントを3〜5個抽出してください。"
                    f"番号付きリスト形式（1. 〇〇）のみで回答してください。"
                    f"各ポイントは1〜2文で簡潔に表現してください。\n\n"
                    f"テキスト:\n{text}"
                ),
            }
        ],
    )

    # 番号付きリストを解析してPythonリストに変換
    lines = response.strip().split('\n')
    key_points = []
    for line in lines:
        # 「1. 」「2. 」などの行を抽出
        match = re.match(r'^\d+\.\s+(.+)', line.strip())
        if match:
            key_points.append(match.group(1))

    # 3〜5個に丸める
    key_points = key_points[:5] if len(key_points) > 5 else key_points

    return key_points


def evaluate_summary(original_text: str, summary: str) -> dict:
    """
    要約の品質を定量的に評価する

    評価指標:
    1. 長さ比率: 要約が元テキストの20〜30%であるか
    2. キーワード包含率: 元テキストの重要語が要約に含まれているか

    CCA試験のポイント:
    - 自動評価を実装することで品質保証を自動化できる
    - 閾値（QUALITY_THRESHOLD）を設定してアラートを出す
    - 品質スコアは後続処理（再要約判断など）に活用できる

    Args:
        original_text: 元のテキスト
        summary: 評価対象の要約

    Returns:
        dict: {length_ratio, keyword_coverage, score, passed}
    """
    # 長さ比率の計算
    length_ratio = len(summary) / len(original_text) if original_text else 0

    # 長さ比率スコア（20〜30%が目標）
    if TARGET_SUMMARY_RATIO_MIN <= length_ratio <= TARGET_SUMMARY_RATIO_MAX:
        length_score = 1.0
    elif length_ratio < TARGET_SUMMARY_RATIO_MIN:
        # 短すぎる: 比率に応じてペナルティ
        length_score = length_ratio / TARGET_SUMMARY_RATIO_MIN
    else:
        # 長すぎる: 比率に応じてペナルティ
        length_score = TARGET_SUMMARY_RATIO_MAX / length_ratio

    # キーワード包含率の計算
    # 元テキストから4文字以上の名詞的な語句を抽出（簡易版）
    # 実際のシステムではMeCabなどの形態素解析器を使う
    words = set(re.findall(r'[ぁ-んァ-ヶー一-龥a-zA-Z]{4,}', original_text))
    if words:
        covered = sum(1 for word in words if word in summary)
        keyword_coverage = covered / len(words)
    else:
        keyword_coverage = 1.0

    # 総合スコア（長さ比率60%、キーワード包含率40%の重み付き平均）
    score = length_score * 0.6 + keyword_coverage * 0.4

    result = {
        "length_ratio": round(length_ratio, 4),
        "length_score": round(length_score, 4),
        "keyword_coverage": round(keyword_coverage, 4),
        "score": round(score, 4),
        "passed": score >= QUALITY_THRESHOLD,
    }

    return result


@dataclass
class DocumentSummarizer:
    """
    ドキュメント要約システム

    チャンク分割・階層的要約・キーポイント抽出・品質評価を
    統合したクラス。
    """

    client: Optional[Anthropic] = field(default=None, repr=False)
    max_chunk_chars: int = MAX_CHUNK_CHARS

    def __post_init__(self) -> None:
        """初期化後処理: クライアントを設定"""
        if self.client is None:
            self.client = get_client()

    def summarize(self, text: str) -> SummaryResult:
        """
        ドキュメントを要約するメインメソッド

        以下の順で処理する:
        1. 形式判定
        2. チャンク分割
        3. 各チャンクの要約（Map）
        4. 全体要約の生成（Reduce）
        5. キーポイント抽出
        6. 品質評価

        Args:
            text: 要約対象のテキスト

        Returns:
            SummaryResult: 要約結果
        """
        print("=" * 60)
        print("📄 ドキュメント要約システム")
        print("=" * 60)
        print(f"入力文字数: {len(text)}文字")

        # 1. 形式判定
        format_type = detect_format(text)
        print(f"検出形式: {format_type}")

        # 2. チャンク分割
        chunks = chunk_text(text, self.max_chunk_chars)

        # 3. 各チャンクを要約（Map段階）
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = summarize_chunk(self.client, chunk, i)
            chunk_summaries.append(summary)

        # 4. 全体要約を生成（Reduce段階）
        if len(chunk_summaries) == 1:
            # チャンクが1つだけの場合はそのまま使用
            final_summary = chunk_summaries[0]
        else:
            final_summary = hierarchical_summarize(self.client, chunk_summaries)

        # 5. キーポイント抽出
        key_points = extract_key_points(self.client, text)

        # 6. 品質評価
        quality_details = evaluate_summary(text, final_summary)
        quality_score = quality_details["score"]

        if not quality_details["passed"]:
            print(f"⚠️ 品質スコアが低い: {quality_score:.2f} (閾値: {QUALITY_THRESHOLD})")

        result = SummaryResult(
            original_text=text,
            format_type=format_type,
            chunk_count=len(chunks),
            chunk_summaries=chunk_summaries,
            final_summary=final_summary,
            key_points=key_points,
            quality_score=quality_score,
            quality_details=quality_details,
        )

        return result

    def print_result(self, result: SummaryResult) -> None:
        """
        要約結果を見やすく出力する

        Args:
            result: SummaryResult オブジェクト
        """
        print("\n" + "=" * 60)
        print("📋 要約結果")
        print("=" * 60)

        print(f"\n📄 入力情報:")
        print(f"  - 形式: {result.format_type}")
        print(f"  - 文字数: {len(result.original_text):,}文字")
        print(f"  - チャンク数: {result.chunk_count}")

        print(f"\n📝 要約 (全体):")
        # 表示を見やすくするため80文字で折り返す
        for line in result.final_summary.split('\n'):
            print(f"  {line}")

        print(f"\n🔑 キーポイント:")
        for i, point in enumerate(result.key_points, 1):
            print(f"  {i}. {point}")

        print(f"\n📊 品質評価:")
        details = result.quality_details
        ratio_pct = details['length_ratio'] * 100
        target_ok = "✅" if TARGET_SUMMARY_RATIO_MIN <= details['length_ratio'] <= TARGET_SUMMARY_RATIO_MAX else "⚠️"
        kw_ok = "✅" if details['keyword_coverage'] >= 0.5 else "⚠️"
        score_ok = "✅" if details['passed'] else "❌"

        print(f"  - 長さ比率: {ratio_pct:.1f}% (目標: {TARGET_SUMMARY_RATIO_MIN * 100:.0f}〜{TARGET_SUMMARY_RATIO_MAX * 100:.0f}%) {target_ok}")
        print(f"  - キーワード包含率: {details['keyword_coverage']:.2f} {kw_ok}")
        print(f"  - 総合スコア: {result.quality_score:.2f} {score_ok}")


# サンプルドキュメント（シナリオ2のテスト用）
SAMPLE_DOCUMENT = """
マイクロサービスアーキテクチャの設計原則

第1章: モノリシックアーキテクチャの課題

従来のモノリシックアーキテクチャでは、すべての機能が単一のコードベースにまとめられています。
この設計は初期開発では生産性が高いですが、システムが成長するにつれて課題が顕在化します。

主な課題として、開発チームの拡大に伴うコードのコンフリクト、一部の機能変更のために全体を
デプロイしなければならない問題、特定のコンポーネントだけをスケールアウトできない問題が挙げられます。
また、特定の技術スタックに縛られるため、新技術の採用が困難になります。

第2章: マイクロサービスアーキテクチャの基本概念

マイクロサービスアーキテクチャとは、アプリケーションを小さな独立したサービスの集合として
設計するアプローチです。各サービスは特定のビジネス機能を担い、独立してデプロイ・スケールできます。

主要な特徴として、サービスの独立性（各サービスが独立して開発・デプロイ・スケール可能）、
疎結合（サービス間の依存を最小化し、API で通信）、高凝集性（各サービスが単一の責務に集中）、
分散データ管理（各サービスが独自のデータストアを持つ）が挙げられます。

第3章: 設計における重要な考慮点

サービスの境界設定は、マイクロサービス設計における最も重要な決定の一つです。
ドメイン駆動設計（DDD）の概念を活用し、ビジネスドメインに沿ったサービス分割が推奨されます。

通信パターンには、同期通信（REST API、gRPC）と非同期通信（メッセージキュー）があります。
非同期通信はサービス間の疎結合を高め、障害の影響を局所化できますが、
結果整合性の管理が複雑になります。

データ管理においては、各サービスが独自のデータベースを持つ「Database per Service」パターンが
推奨されます。これにより、サービスの独立性が保たれますが、分散トランザクションの管理が課題となります。

第4章: 実装時の課題と対策

マイクロサービスの実装では、サービスディスカバリー（動的なサービスの位置情報の管理）、
ロードバランシング（複数インスタンス間のトラフィック分散）、サーキットブレーカー（障害の連鎖防止）、
分散トレーシング（複数サービスにまたがるリクエストの追跡）などの横断的関心事に対応する必要があります。

これらの複雑さを管理するために、Kubernetes などのコンテナオーケストレーションプラットフォームや、
Istio などのサービスメッシュの採用が増えています。

第5章: まとめ

マイクロサービスアーキテクチャは、大規模で複雑なシステムの開発・運用において強力なアプローチです。
ただし、分散システム固有の複雑さが増加するため、小規模チームや単純なシステムには適さない場合があります。
組織の規模、技術的な成熟度、ビジネス要件を総合的に考慮した上で採用を判断してください。
""".strip()


def main() -> None:
    """
    ドキュメント要約システムのデモ実行

    サンプルドキュメントを使って全機能をデモします。
    Google Colab で実行する場合は、この関数を呼び出すだけでOKです。
    """
    summarizer = DocumentSummarizer()

    # サンプルドキュメントで要約を実行
    result = summarizer.summarize(SAMPLE_DOCUMENT)

    # 結果を表示
    summarizer.print_result(result)

    print("\n✅ デモ完了！")
    print("\n--- 追加テスト: 形式判定 ---")
    markdown_text = "# 見出し\n\n**太字** テキストです。"
    structured_text = "第1章: 概要\n\n・ポイント1\n・ポイント2"
    plain_text = "これは通常のテキストです。"

    for text, expected in [
        (markdown_text, "markdown"),
        (structured_text, "structured"),
        (plain_text, "plaintext"),
    ]:
        detected = detect_format(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{text[:20]}...' → {detected} (期待: {expected})")


if __name__ == "__main__":
    main()
