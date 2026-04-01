"""
02_pii_handling.py - 個人情報（PII）の検出とマスキング

このファイルの目的:
- メールアドレス・電話番号・クレジットカード番号・住所の自動検出を学ぶ
- 正規表現を使ったPIIのマスキング方法を理解する
- データ匿名化の実践的な実装方法を習得する
- APIにPIIを送信しないためのベストプラクティスを学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 03_secure_applications/02_pii_handling.py

【PIIとは？】
PII（Personally Identifiable Information）とは、個人を識別できる情報のことです。
- メールアドレス、電話番号、クレジットカード番号、住所、氏名など
- AIに送信されたPIIはモデルの学習や記録に使用される可能性があります
- 適切なマスキングにより、プライバシーとコンプライアンスを保護できます
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional

from anthropic import Anthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"


@dataclass
class PIIDetectionResult:
    """PII検出結果を格納するデータクラス"""
    original_text: str          # 元のテキスト
    masked_text: str            # マスキング後のテキスト
    detected_items: list[dict]  # 検出されたPIIの詳細リスト
    has_pii: bool               # PIIが含まれているかどうか

    def __post_init__(self) -> None:
        self.has_pii = len(self.detected_items) > 0


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


# ============================================================
# PII検出用の正規表現パターン
# ============================================================

# メールアドレスのパターン
# RFC 5321に準拠した一般的なメールアドレスを検出
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
)

# 日本の電話番号パターン（ハイフンあり・なし両対応）
# 例: 03-1234-5678, 090-1234-5678, 0312345678
PHONE_PATTERN_JP = re.compile(
    r'(?<!\d)(?:'
    r'0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{4}'  # 固定電話・携帯
    r'|0\d{9,10}'                          # ハイフンなし
    r')(?!\d)'
)

# クレジットカード番号パターン
# 主要カードブランド（Visa, Mastercard, Amex, JCBなど）に対応
CREDIT_CARD_PATTERN = re.compile(
    r'\b(?:'
    r'4[0-9]{3}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}'   # Visa
    r'|5[1-5][0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}'  # Mastercard
    r'|3[47][0-9]{2}[-\s]?[0-9]{6}[-\s]?[0-9]{5}'              # Amex
    r'|3(?:0[0-5]|[68][0-9])[0-9]{1}[-\s]?[0-9]{6}[-\s]?[0-9]{4}'  # Diners
    r'|(?:2131|1800|35\d{3})[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{3}'  # JCB
    r')\b'
)

# 日本の郵便番号パターン
POSTAL_CODE_PATTERN_JP = re.compile(
    r'〒?\s*\d{3}[-−]\d{4}'
)

# 日本の住所パターン（都道府県から始まる住所）
ADDRESS_PATTERN_JP = re.compile(
    r'(?:北海道|青森|岩手|宮城|秋田|山形|福島|'
    r'茨城|栃木|群馬|埼玉|千葉|東京|神奈川|'
    r'新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|'
    r'三重|滋賀|京都|大阪|兵庫|奈良|和歌山|'
    r'鳥取|島根|岡山|広島|山口|'
    r'徳島|香川|愛媛|高知|'
    r'福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島|沖縄)'
    r'(?:都|道|府|県)?[^\n]{5,50}'
)

# マイナンバー（個人番号）パターン
MY_NUMBER_PATTERN = re.compile(
    r'(?:マイナンバー|個人番号)[：:\s]*\d{4}[-\s]?\d{4}[-\s]?\d{4}'
    r'|\b\d{4}[-\s]\d{4}[-\s]\d{4}\b'  # ハイフン区切り12桁
)


def detect_and_mask_email(text: str) -> tuple[str, list[dict]]:
    """
    メールアドレスを検出してマスキングする

    Args:
        text: 処理するテキスト

    Returns:
        tuple[str, list[dict]]: (マスキング後テキスト, 検出されたPIIリスト)
    """
    detected = []
    masked = text

    for match in EMAIL_PATTERN.finditer(text):
        email = match.group()
        # ユーザー名の部分を*** でマスク（ドメインは残す）
        parts = email.split('@')
        masked_email = f"***@{parts[1]}" if len(parts) == 2 else "***@***.***"

        detected.append({
            "type": "メールアドレス",
            "original": email,
            "masked": masked_email,
            "position": (match.start(), match.end())
        })
        masked = masked.replace(email, masked_email, 1)

    return masked, detected


def detect_and_mask_phone(text: str) -> tuple[str, list[dict]]:
    """
    電話番号を検出してマスキングする

    Args:
        text: 処理するテキスト

    Returns:
        tuple[str, list[dict]]: (マスキング後テキスト, 検出されたPIIリスト)
    """
    detected = []
    masked = text

    for match in PHONE_PATTERN_JP.finditer(text):
        phone = match.group()
        # 最初の3桁と最後の4桁を残してマスク
        digits_only = re.sub(r'[-\s]', '', phone)
        if len(digits_only) >= 7:
            masked_phone = digits_only[:3] + "-****-" + digits_only[-4:]
        else:
            masked_phone = "***-****-****"

        detected.append({
            "type": "電話番号",
            "original": phone,
            "masked": masked_phone,
            "position": (match.start(), match.end())
        })
        masked = masked.replace(phone, masked_phone, 1)

    return masked, detected


def detect_and_mask_credit_card(text: str) -> tuple[str, list[dict]]:
    """
    クレジットカード番号を検出してマスキングする

    Args:
        text: 処理するテキスト

    Returns:
        tuple[str, list[dict]]: (マスキング後テキスト, 検出されたPIIリスト)
    """
    detected = []
    masked = text

    for match in CREDIT_CARD_PATTERN.finditer(text):
        card = match.group()
        # 最初の4桁と最後の4桁のみ残してマスク（PCI DSS準拠）
        digits_only = re.sub(r'[-\s]', '', card)
        if len(digits_only) >= 8:
            masked_card = digits_only[:4] + "-****-****-" + digits_only[-4:]
        else:
            masked_card = "****-****-****-****"

        detected.append({
            "type": "クレジットカード番号",
            "original": card,
            "masked": masked_card,
            "position": (match.start(), match.end())
        })
        masked = masked.replace(card, masked_card, 1)

    return masked, detected


def detect_and_mask_address(text: str) -> tuple[str, list[dict]]:
    """
    住所を検出してマスキングする

    Args:
        text: 処理するテキスト

    Returns:
        tuple[str, list[dict]]: (マスキング後テキスト, 検出されたPIIリスト)
    """
    detected = []
    masked = text

    # 郵便番号のマスキング
    for match in POSTAL_CODE_PATTERN_JP.finditer(text):
        postal = match.group()
        masked_postal = "〒***-****"
        detected.append({
            "type": "郵便番号",
            "original": postal,
            "masked": masked_postal,
            "position": (match.start(), match.end())
        })
        masked = masked.replace(postal, masked_postal, 1)

    # 住所のマスキング（都道府県名から始まる部分）
    for match in ADDRESS_PATTERN_JP.finditer(masked):
        address = match.group()
        # 都道府県名だけ残してマスク
        pref = address[:3] if len(address) >= 3 else address
        masked_address = pref + "***"
        detected.append({
            "type": "住所",
            "original": address,
            "masked": masked_address,
            "position": (match.start(), match.end())
        })
        masked = masked.replace(address, masked_address, 1)

    return masked, detected


def detect_and_mask_pii(text: str) -> PIIDetectionResult:
    """
    テキスト全体からPIIを検出してマスキングする統合関数

    これが実際のアプリケーションで使う主要関数です。
    すべてのPIIタイプをまとめて処理します。

    Args:
        text: 処理するテキスト

    Returns:
        PIIDetectionResult: 検出・マスキング結果
    """
    all_detected = []
    masked = text

    # 各PII種別を順番に処理
    # ※クレジットカードを先に処理（数字の連続が電話番号と混同される可能性があるため）
    masked, cc_detected = detect_and_mask_credit_card(masked)
    all_detected.extend(cc_detected)

    masked, email_detected = detect_and_mask_email(masked)
    all_detected.extend(email_detected)

    masked, phone_detected = detect_and_mask_phone(masked)
    all_detected.extend(phone_detected)

    masked, addr_detected = detect_and_mask_address(masked)
    all_detected.extend(addr_detected)

    return PIIDetectionResult(
        original_text=text,
        masked_text=masked,
        detected_items=all_detected,
        has_pii=False  # __post_init__ で自動設定される
    )


def safe_api_call_with_pii_masking(
    client: Anthropic,
    user_message: str,
    system_prompt: Optional[str] = None
) -> dict:
    """
    PIIをマスキングしてからAPIを呼び出す安全な関数

    Args:
        client: Anthropicクライアント
        user_message: ユーザーメッセージ
        system_prompt: システムプロンプト（オプション）

    Returns:
        dict: {
            "response": APIレスポンス,
            "pii_detected": PIIが検出されたかどうか,
            "pii_count": 検出されたPIIの数,
            "masked_message": マスキング後のメッセージ
        }
    """
    # PIIを検出してマスキング
    result = detect_and_mask_pii(user_message)

    if result.has_pii:
        print(f"⚠️  PIIを検出・マスキングしました（{len(result.detected_items)}件）")
        for item in result.detected_items:
            print(f"   - {item['type']}: {item['original']} → {item['masked']}")

    # APIパラメータ
    request_params = {
        "model": MODEL_NAME,
        "max_tokens": 512,
        "messages": [
            {"role": "user", "content": result.masked_text}  # マスキング後テキストを送信
        ]
    }
    if system_prompt:
        request_params["system"] = system_prompt

    try:
        response = client.messages.create(**request_params)
        api_response = response.content[0].text
    except Exception as e:
        api_response = f"❌ APIエラー: {e}"

    return {
        "response": api_response,
        "pii_detected": result.has_pii,
        "pii_count": len(result.detected_items),
        "masked_message": result.masked_text
    }


def demonstrate_pii_detection() -> None:
    """
    PII検出とマスキングのデモを行う（APIなし）
    """
    print("\n--- PII検出とマスキングのデモ ---")

    # 様々なPIIを含むテスト文章
    test_texts = [
        # メールアドレス
        "お問い合わせは tanaka.taro@example.co.jp までご連絡ください。",
        # 電話番号（複数形式）
        "連絡先: 03-1234-5678 または 090-9876-5432",
        # クレジットカード番号
        "カード番号: 4532 1234 5678 9012 の支払いを処理してください。",
        # 住所
        "お届け先: 〒100-0001 東京都千代田区千代田1-1",
        # 複合（複数のPIIを含む）
        (
            "田中太郎様\n"
            "メール: taro.tanaka@company.jp\n"
            "電話: 080-1234-5678\n"
            "住所: 〒530-0001 大阪府大阪市北区梅田1-1-1\n"
            "カード: 5423 1234 5678 9012"
        ),
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\n[テスト {i}]")
        print(f"元のテキスト:\n{text}")

        result = detect_and_mask_pii(text)

        print(f"\nマスキング後:\n{result.masked_text}")
        print(f"\n検出されたPII ({len(result.detected_items)}件):")
        for item in result.detected_items:
            print(f"  - {item['type']}: {item['original']} → {item['masked']}")
        print("-" * 40)


def demonstrate_safe_api_call(client: Anthropic) -> None:
    """
    PIIマスキング付きAPIコールのデモ

    Args:
        client: Anthropicクライアント
    """
    print("\n--- PIIマスキング付きAPIコールのデモ ---")

    # PIIを含むメッセージ（実際のユーザー入力を想定）
    user_message = (
        "私は山田花子（yamada.hanako@example.com）です。"
        "電話番号は 090-1111-2222 で、"
        "東京都新宿区新宿1-1-1に住んでいます。"
        "メールが届かない原因を調べてもらえますか？"
    )

    print(f"ユーザーの入力:\n{user_message}\n")

    result = safe_api_call_with_pii_masking(
        client,
        user_message,
        system_prompt="あなたはメールのトラブルシューティングを専門とするサポートエージェントです。"
    )

    print(f"\nAPIに送信されたメッセージ（マスキング後）:\n{result['masked_message']}")
    print(f"\nClaudeの応答:\n{result['response']}")


def pii_best_practices() -> None:
    """
    PII取り扱いのベストプラクティスを表示する
    """
    print("\n--- PII取り扱いのベストプラクティス ---")

    best_practices = """
【✅ PII取り扱いのポイント】

1. APIに送信する前にマスキングする
   - ユーザー入力にPIIが含まれる可能性を常に想定する
   - Anthropicのポリシー上、APIに不必要なPIIを送信しないことが推奨される
   - マスキングは不可逆な形式で行う

2. 正規表現による自動検出を活用する
   - メールアドレス、電話番号、クレジットカード番号は正規表現で高精度に検出可能
   - 日本固有の形式（日本の電話番号、住所形式など）に対応したパターンを使う
   - 定期的にパターンを見直し・更新する

3. PCI DSS準拠のマスキング（クレジットカード）
   - カード番号は最初の6桁と最後の4桁のみ保持（PCI DSS要件）
   - または最初の4桁と最後の4桁のみ
   - 絶対に完全なカード番号をログに記録しない

4. データ匿名化の種類を理解する
   - マスキング: 一部を*** で置き換える（部分的に情報を保持）
   - 仮名化: ランダムな値に置き換える（統計分析に使用可能）
   - 完全削除: PIIを含む部分を削除（最も安全だが情報損失あり）

5. ログにPIIを含めない
   - APIリクエスト・レスポンスのロギング時も注意
   - マスキング後のデータのみをログに記録する

【⚠️ よくある間違い】

1. クライアントサイドのみのマスキング → サーバー側でも実施する
2. 不完全な正規表現 → テストケースを十分に用意する
3. マスキングのバイパス → マスキング後も再チェックを行う
4. ログへのPII記録 → ロギング時も必ずマスキングを適用

【💡 CCA試験のポイント】
- APIに個人情報を送信するリスクとポリシーを理解する
- PIIマスキングはAnthropicの利用規約への準拠にも関係する
- 正規表現によるPII検出は実用的なアプローチ
- 「最小権限の原則」: AIに必要以上の情報を渡さない
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 60)
    print("個人情報（PII）の検出とマスキング")
    print("=" * 60)

    # PII検出のデモ（APIなし）
    demonstrate_pii_detection()

    # ベストプラクティスの表示（APIなし）
    pii_best_practices()

    # APIを使ったデモ
    print("\n--- API接続テスト ---")
    client = get_client()
    demonstrate_safe_api_call(client)

    print("\n✅ 完了！次は03_error_handling.pyに進んでください。")
