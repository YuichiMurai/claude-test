"""
scenario_01_solution.py - カスタマーサポートチャットボット（模範解答）

【このファイルの目的】
シナリオ1「カスタマーサポートチャットボットの構築」の模範解答です。
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
- マルチターン会話はメッセージリストに履歴を追加するだけで実現できる
- 感情分析にはClaudeにJSON形式で返答させると解析が簡単
- FAQはシンプルなキーワードマッチで十分実用的
- エスカレーション条件を明確に定義することが設計の鍵
- 会話ログはJSONで保存するとデバッグや分析に活用できる

【CCA試験でのポイント】
- システムプロンプトでボットの役割・制約・トーンを明確に定義する
- 感情に応じたレスポンス変更はUXに直結する重要な設計判断
- エスカレーションは過剰でも不足でもいけない（適切な閾値設定）
- 会話ログは監査・品質改善に不可欠なセキュリティ要件
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import anthropic
from anthropic import Anthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"

# 会話の最大ターン数
MAX_TURNS = 10

# エスカレーション判定の閾値
ESCALATION_REPEAT_THRESHOLD = 3  # 同じ問題を何回繰り返したらエスカレーションするか

# FAQデータ（実際のシステムではDBから取得する）
FAQ_DATA = [
    {
        "id": "faq_001",
        "question": "注文のキャンセルはできますか？",
        "answer": "注文確定後24時間以内であればキャンセル可能です。マイページ→注文履歴からお手続きください。",
        "keywords": ["キャンセル", "取り消し", "注文"],
    },
    {
        "id": "faq_002",
        "question": "返品・返金のポリシーを教えてください",
        "answer": "商品到着後7日以内であれば返品可能です。未開封・未使用の場合に限ります。返送料はお客様負担となります。",
        "keywords": ["返品", "返金", "交換", "払い戻し"],
    },
    {
        "id": "faq_003",
        "question": "配送にはどのくらいかかりますか？",
        "answer": "通常配送は3〜5営業日、速達配送は翌日〜2営業日でお届けします。",
        "keywords": ["配送", "届く", "発送", "到着", "いつ"],
    },
    {
        "id": "faq_004",
        "question": "支払い方法は何が使えますか？",
        "answer": "クレジットカード（VISA/Mastercard/JCB）、コンビニ払い、銀行振込、PayPayに対応しています。",
        "keywords": ["支払い", "決済", "クレジット", "PayPay", "振込"],
    },
    {
        "id": "faq_005",
        "question": "商品の在庫状況を確認したい",
        "answer": "商品ページで在庫状況をリアルタイムで確認できます。在庫切れの場合は「入荷通知」に登録できます。",
        "keywords": ["在庫", "品切れ", "売り切れ", "在庫確認"],
    },
    {
        "id": "faq_006",
        "question": "会員登録のメリットは？",
        "answer": "会員登録でポイントが貯まり、購入時に利用できます。また、注文履歴の管理や再注文が簡単になります。",
        "keywords": ["会員", "登録", "ポイント", "アカウント"],
    },
    {
        "id": "faq_007",
        "question": "パスワードを忘れました",
        "answer": "ログインページの「パスワードを忘れた方」からリセット手続きができます。登録済みメールアドレスに再設定リンクをお送りします。",
        "keywords": ["パスワード", "ログイン", "忘れ", "リセット"],
    },
    {
        "id": "faq_008",
        "question": "領収書の発行はできますか？",
        "answer": "マイページ→注文履歴→対象注文の「領収書」ボタンから PDF でダウンロードできます。",
        "keywords": ["領収書", "領収", "請求書", "経費"],
    },
]


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
class ConversationEntry:
    """会話の1エントリを表すデータクラス"""

    timestamp: str
    role: str          # "user" または "assistant"
    content: str
    sentiment: Optional[str] = None   # "positive" / "negative" / "neutral"
    faq_matched: Optional[str] = None  # マッチしたFAQ ID
    escalated: bool = False


@dataclass
class CustomerSupportBot:
    """
    カスタマーサポートチャットボット

    マルチターン会話・感情分析・FAQ検索・エスカレーション判定・
    会話ログ保存を統合したクラス。
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    conversation_history: list = field(default_factory=list)
    conversation_log: list = field(default_factory=list)
    turn_count: int = 0
    escalation_flag: bool = False
    client: Optional[Anthropic] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """初期化後処理: クライアントとシステムプロンプトを設定"""
        if self.client is None:
            self.client = get_client()

    def _build_system_prompt(self) -> str:
        """
        システムプロンプトを構築する

        CCA試験のポイント:
        - ロール定義（何者か）
        - 制約（やらないこと）
        - トーン（話し方）
        - エスカレーション条件
        を明示的に定義することが重要。
        """
        return """あなたはECサイト「TechMart」のカスタマーサポートAIです。

# 役割
- TechMartの注文・返品・配送・アカウントに関する問い合わせに対応します
- 丁寧で親切な日本語で応答します
- 問題解決を最優先に考えます

# 対応方針
- ユーザーが怒っている・不満を感じている場合は、まず謝罪と共感を示してから解決策を提案します
- 具体的な注文番号や商品名を聞いて、正確な情報を提供します
- 解決できない問題は正直に伝え、人間のサポート担当者への引き継ぎを提案します

# 制約
- 個人情報（クレジットカード番号、銀行口座等）を直接聞いたり記録したりしません
- TechMart以外のサービスに関する質問には対応しません
- 常に礼儀正しく、攻撃的な言動には毅然と丁寧に対応します"""

    def analyze_sentiment(self, text: str) -> dict:
        """
        ユーザーの感情を分析する

        CCA試験のポイント:
        - ClaudeにJSON形式で返答させると解析が容易
        - 感情分析は別のAPIコールで行う（精度向上のため）
        - エラー時はデフォルト値（neutral）を返す

        Args:
            text: 分析対象のテキスト

        Returns:
            dict: 感情分析結果 {sentiment, confidence, reason}
        """
        try:
            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=256,
                messages=[
                    {
                        "role": "user",
                        "content": f"""以下のテキストの感情を分析してください。
JSON形式のみで回答してください（説明不要）。

テキスト: 「{text}」

回答形式:
{{
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0〜1.0の数値,
  "reason": "判断理由（日本語・20文字以内）"
}}""",
                    }
                ],
            )

            result = json.loads(response.content[0].text)
            return result

        except (json.JSONDecodeError, anthropic.APIError) as e:
            # エラー時はニュートラルをデフォルトとして返す
            print(f"⚠️ 感情分析エラー: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "reason": "分析エラー"}

    def search_faq(self, user_message: str) -> Optional[dict]:
        """
        FAQデータからユーザーの質問に関連するエントリを検索する

        CCA試験のポイント:
        - シンプルなキーワードマッチで十分実用的
        - 複数マッチした場合は最もキーワード数が多いものを返す
        - 大文字小文字を区別しない検索が基本

        Args:
            user_message: ユーザーのメッセージ

        Returns:
            dict | None: マッチしたFAQエントリ、なければNone
        """
        best_match = None
        best_match_count = 0

        for faq in FAQ_DATA:
            # キーワードがいくつマッチするか数える
            match_count = sum(
                1 for keyword in faq["keywords"]
                if keyword in user_message
            )

            if match_count > best_match_count:
                best_match_count = match_count
                best_match = faq

        # 1つもマッチしなければNoneを返す
        return best_match if best_match_count > 0 else None

    def should_escalate(
        self,
        user_message: str,
        sentiment: dict,
    ) -> tuple[bool, str]:
        """
        人間のサポートにエスカレーションすべきか判定する

        エスカレーション条件:
        1. ユーザーが明示的に人間のサポートを要求している
        2. ユーザーが強い怒りを示している（negative + confidence >= 0.8）
        3. 同じ問題について繰り返し（ESCALATION_REPEAT_THRESHOLD回以上）やり取りしている

        CCA試験のポイント:
        - エスカレーション条件を明確に文書化することが重要
        - 過剰エスカレーションはコスト増、不足は顧客不満に直結

        Args:
            user_message: ユーザーのメッセージ
            sentiment: 感情分析結果

        Returns:
            tuple[bool, str]: (エスカレーションすべきか, 理由)
        """
        # 条件1: ユーザーが明示的に人間のサポートを要求
        human_request_keywords = [
            "人間", "担当者", "オペレーター", "スタッフ",
            "直接話したい", "電話", "つないで", "替わって"
        ]
        if any(keyword in user_message for keyword in human_request_keywords):
            return True, "ユーザーが人間のサポートを要求しています"

        # 条件2: 強い怒りを示している
        if (
            sentiment.get("sentiment") == "negative"
            and sentiment.get("confidence", 0) >= 0.8
        ):
            return True, "ユーザーが強い怒りを示しています"

        # 条件3: 会話が繰り返し続いている（閾値を超えたターン数）
        if self.turn_count >= ESCALATION_REPEAT_THRESHOLD:
            return True, f"{ESCALATION_REPEAT_THRESHOLD}回以上やり取りが続いています"

        return False, ""

    def chat(self, user_message: str) -> str:
        """
        ユーザーメッセージを受け取り、ボットの応答を生成する

        メインのエントリポイント。感情分析→FAQ検索→エスカレーション判定→
        応答生成の順で処理する。

        Args:
            user_message: ユーザーのメッセージ

        Returns:
            str: ボットの応答テキスト

        Raises:
            RuntimeError: 最大ターン数を超えた場合
        """
        # 最大ターン数チェック
        if self.turn_count >= MAX_TURNS:
            self._save_conversation()
            raise RuntimeError(
                f"会話が最大ターン数（{MAX_TURNS}）を超えました。会話をリセットします。"
            )

        # 感情分析
        sentiment = self.analyze_sentiment(user_message)
        print(f"  [感情分析] {sentiment['sentiment']} (信頼度: {sentiment['confidence']:.2f})")

        # FAQ検索
        matched_faq = self.search_faq(user_message)
        faq_context = ""
        if matched_faq:
            faq_context = f"\n\n[FAQ情報]\nQ: {matched_faq['question']}\nA: {matched_faq['answer']}"
            print(f"  [FAQ] マッチ: {matched_faq['id']}")

        # エスカレーション判定
        should_esc, esc_reason = self.should_escalate(user_message, sentiment)
        if should_esc and not self.escalation_flag:
            self.escalation_flag = True
            print(f"  [エスカレーション] 必要と判断: {esc_reason}")

        # 会話履歴にユーザーメッセージを追加
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # ログに記録
        self.conversation_log.append(ConversationEntry(
            timestamp=datetime.now().isoformat(),
            role="user",
            content=user_message,
            sentiment=sentiment["sentiment"],
            faq_matched=matched_faq["id"] if matched_faq else None,
            escalated=self.escalation_flag,
        ))

        # エスカレーションが必要な場合は特別な応答を生成
        if self.escalation_flag and should_esc:
            escalation_message = (
                "ご不便をおかけして申し訳ございません。"
                "より専門的なサポートが必要と判断しました。"
                "担当スタッフにお繋ぎしますので、少々お待ちください。\n\n"
                f"（引き継ぎ理由: {esc_reason}）"
            )
            # エスカレーション応答をログに記録して返す
            self.conversation_log.append(ConversationEntry(
                timestamp=datetime.now().isoformat(),
                role="assistant",
                content=escalation_message,
                escalated=True,
            ))
            self.turn_count += 1
            self._save_conversation()
            return escalation_message

        # ネガティブな感情の場合はシステムプロンプトに追記
        sentiment_instruction = ""
        if sentiment["sentiment"] == "negative":
            sentiment_instruction = "\n\n[内部指示] ユーザーが不満を感じています。まず共感・謝罪を示してください。"

        # FAQ情報とシステムプロンプトをまとめる
        system_content = self._build_system_prompt() + faq_context + sentiment_instruction

        try:
            # Claude API を呼び出して応答を生成
            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=512,
                system=system_content,
                messages=self.conversation_history,
            )
            bot_response = response.content[0].text

        except anthropic.RateLimitError:
            # レート制限エラー: 待機してリトライ
            print("⚠️ レート制限に達しました。60秒後にリトライします...")
            time.sleep(60)
            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=512,
                system=system_content,
                messages=self.conversation_history,
            )
            bot_response = response.content[0].text

        except anthropic.APIError as e:
            bot_response = f"申し訳ありません、現在システムに問題が発生しています。（エラー: {e}）"

        # 会話履歴にボットの応答を追加
        self.conversation_history.append({
            "role": "assistant",
            "content": bot_response,
        })

        # ログに記録
        self.conversation_log.append(ConversationEntry(
            timestamp=datetime.now().isoformat(),
            role="assistant",
            content=bot_response,
        ))

        self.turn_count += 1
        return bot_response

    def save_conversation(self) -> str:
        """
        会話履歴をJSONファイルに保存する（公開インターフェース）

        Returns:
            str: 保存したファイルのパス
        """
        return self._save_conversation()

    def _save_conversation(self) -> str:
        """
        会話履歴をJSONファイルに保存する（内部実装）

        CCA試験のポイント:
        - 会話ログは監査・品質改善・コンプライアンスに不可欠
        - セッションIDでファイルを一意に識別する
        - タイムスタンプで時系列を把握できるようにする

        Returns:
            str: 保存したファイルのパス
        """
        filename = f"conversation_log_{self.session_id}.json"
        log_data = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "turn_count": self.turn_count,
            "escalated": self.escalation_flag,
            "entries": [
                {
                    "timestamp": entry.timestamp,
                    "role": entry.role,
                    "content": entry.content,
                    "sentiment": entry.sentiment,
                    "faq_matched": entry.faq_matched,
                    "escalated": entry.escalated,
                }
                for entry in self.conversation_log
            ],
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        print(f"💾 会話ログを保存しました: {filename}")
        return filename


def main() -> None:
    """
    カスタマーサポートチャットボットのデモ実行

    実際の会話フローをシミュレートします。
    Google Colab で実行する場合は、この関数を呼び出すだけでOKです。
    """
    print("=" * 60)
    print("🤖 TechMart カスタマーサポートチャットボット")
    print("=" * 60)
    print("（'quit' で終了、'reset' で会話リセット）\n")

    bot = CustomerSupportBot()
    print(f"セッションID: {bot.session_id}\n")

    # デモ用の事前定義された会話シナリオ
    demo_conversation = [
        "こんにちは！先日注文した商品がまだ届かないのですが...",
        "注文番号は #TM-56789 です。もう1週間経つのに届きません！",
        "返品したい場合はどうすればいいですか？",
        "担当者に直接話したいのですが",
    ]

    for user_input in demo_conversation:
        print(f"👤 ユーザー: {user_input}")
        try:
            response = bot.chat(user_input)
            print(f"🤖 ボット: {response}")
            print()
        except RuntimeError as e:
            print(f"⚠️ {e}")
            break

    # 会話ログを保存
    log_file = bot.save_conversation()
    print(f"\n✅ デモ完了。ログファイル: {log_file}")

    # インタラクティブモード（Colabで動作確認する場合）
    # print("\n--- インタラクティブモード ---")
    # while True:
    #     user_input = input("👤 あなた: ").strip()
    #     if user_input.lower() == 'quit':
    #         bot.save_conversation()
    #         break
    #     if user_input.lower() == 'reset':
    #         bot.save_conversation()
    #         bot = CustomerSupportBot()
    #         print("🔄 会話をリセットしました")
    #         continue
    #     if user_input:
    #         response = bot.chat(user_input)
    #         print(f"🤖 ボット: {response}\n")


if __name__ == "__main__":
    main()
