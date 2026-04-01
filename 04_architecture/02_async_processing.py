"""
02_async_processing.py - 非同期処理

このファイルの目的:
- asyncio を使って複数のAPIリクエストを並行実行する方法を学ぶ
- 同期処理と非同期処理のパフォーマンスを比較する
- タイムアウト処理の実装方法を習得する
- エラーハンドリングの非同期版を理解する

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv nest_asyncio -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. Colabではイベントループが既に動いているため、nest_asyncio が必要です:
   import nest_asyncio
   nest_asyncio.apply()

4. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 04_architecture/02_async_processing.py

【非同期処理が重要な理由】
同期処理では複数のAPIリクエストが直列に実行されます。
例えば10個のリクエストがそれぞれ1秒かかる場合:
  同期処理: 10秒 × 1 = 10秒
  非同期処理: 約1秒（並行実行）

非同期処理により大幅なパフォーマンス改善が可能です。
"""

import asyncio
import os
import time
from typing import Optional

from anthropic import Anthropic, AsyncAnthropic

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


def get_async_client() -> AsyncAnthropic:
    """
    非同期APIクライアントを取得する（Colab・ローカル両対応）

    AsyncAnthropic は非同期処理用のクライアント。
    async/await 構文と一緒に使用する。
    """
    try:
        from google.colab import userdata
        api_key = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')

    return AsyncAnthropic(api_key=api_key)


# =============================================================================
# 1. 基本的な非同期処理
# =============================================================================

async def async_query(
    client: AsyncAnthropic,
    prompt: str,
    max_tokens: int = 256,
    request_id: Optional[int] = None
) -> dict:
    """
    非同期APIクエリ

    async def で定義された関数はコルーチンになります。
    await で呼び出すと、レスポンスを待っている間に
    他のコルーチンが実行できます（協調的マルチタスク）。

    Args:
        client: 非同期Anthropicクライアント
        prompt: ユーザーのプロンプト
        max_tokens: 最大トークン数
        request_id: リクエスト識別子（デバッグ用）

    Returns:
        dict: {
            "id": リクエストID,
            "prompt": プロンプト,
            "text": レスポンステキスト,
            "elapsed": 処理時間（秒）
        }
    """
    start = time.time()
    # await でAPIレスポンスを待つ
    # この間に他のコルーチンが実行される（非同期の核心）
    response = await client.messages.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start

    return {
        "id": request_id,
        "prompt": prompt[:40],
        "text": response.content[0].text,
        "elapsed": elapsed,
    }


async def async_query_with_timeout(
    client: AsyncAnthropic,
    prompt: str,
    max_tokens: int = 256,
    timeout: float = 30.0,
    request_id: Optional[int] = None
) -> dict:
    """
    タイムアウト付き非同期APIクエリ

    asyncio.wait_for() でタイムアウトを設定。
    指定時間内にレスポンスがなければ TimeoutError を発生させる。

    Args:
        client: 非同期Anthropicクライアント
        prompt: ユーザーのプロンプト
        max_tokens: 最大トークン数
        timeout: タイムアウト時間（秒）
        request_id: リクエスト識別子

    Returns:
        dict: レスポンス情報（タイムアウト時はエラー情報）
    """
    start = time.time()
    try:
        # asyncio.wait_for: タイムアウト付き実行
        # timeout 秒以内にコルーチンが完了しない場合は
        # asyncio.TimeoutError を発生させる
        response = await asyncio.wait_for(
            client.messages.create(
                model=MODEL_NAME,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            ),
            timeout=timeout
        )
        elapsed = time.time() - start
        return {
            "id": request_id,
            "prompt": prompt[:40],
            "text": response.content[0].text,
            "elapsed": elapsed,
            "error": None
        }

    except asyncio.TimeoutError:
        elapsed = time.time() - start
        return {
            "id": request_id,
            "prompt": prompt[:40],
            "text": None,
            "elapsed": elapsed,
            "error": f"タイムアウト（{timeout}秒）"
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "id": request_id,
            "prompt": prompt[:40],
            "text": None,
            "elapsed": elapsed,
            "error": str(e)
        }


# =============================================================================
# 2. 並行処理のデモ
# =============================================================================

async def run_sequential(
    client: AsyncAnthropic,
    prompts: list[str],
    max_tokens: int = 100
) -> list[dict]:
    """
    逐次処理（参考: 非同期処理との比較用）

    awaitを使っているが、1つずつ順番に処理するため
    並行実行の恩恵を受けない。

    Args:
        client: 非同期Anthropicクライアント
        prompts: プロンプトのリスト
        max_tokens: 最大トークン数

    Returns:
        list[dict]: 各リクエストの結果
    """
    results = []
    for i, prompt in enumerate(prompts):
        # awaitで1つずつ処理（逐次）
        result = await async_query(client, prompt, max_tokens, request_id=i + 1)
        results.append(result)
    return results


async def run_concurrent(
    client: AsyncAnthropic,
    prompts: list[str],
    max_tokens: int = 100
) -> list[dict]:
    """
    並行処理（asyncio.gather を使用）

    asyncio.gather() は複数のコルーチンを並行して実行する。
    すべてのコルーチンが完了するまで待機し、結果を順番通りに返す。

    これにより、N個のリクエストをほぼ同時に送信し、
    最も遅いリクエストの時間で完了できる。

    Args:
        client: 非同期Anthropicクライアント
        prompts: プロンプトのリスト
        max_tokens: 最大トークン数

    Returns:
        list[dict]: 各リクエストの結果（プロンプトの順序通り）
    """
    # タスクのリストを作成
    tasks = [
        async_query(client, prompt, max_tokens, request_id=i + 1)
        for i, prompt in enumerate(prompts)
    ]

    # asyncio.gather: 全タスクを並行実行し、全完了を待つ
    # return_exceptions=False（デフォルト）: 例外が発生した場合は即座に伝播する
    # ※ return_exceptions=True にすると例外も結果として収集できる（run_with_error_handling で使用）
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)


async def run_concurrent_with_limit(
    client: AsyncAnthropic,
    prompts: list[str],
    max_tokens: int = 100,
    max_concurrent: int = 3
) -> list[dict]:
    """
    同時実行数を制限した並行処理

    asyncio.Semaphore を使って同時実行数を制御する。
    レート制限を守りながら並行処理するために使用。

    Args:
        client: 非同期Anthropicクライアント
        prompts: プロンプトのリスト
        max_tokens: 最大トークン数
        max_concurrent: 最大同時実行数

    Returns:
        list[dict]: 各リクエストの結果
    """
    # Semaphore: 同時実行数を制限するカウンタ
    # max_concurrent=3 の場合、同時に3つのコルーチンのみが実行できる
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_query(prompt: str, request_id: int) -> dict:
        """Semaphore で制限されたクエリ"""
        async with semaphore:
            # Semaphore のカウントが0になると、ここで待機する
            return await async_query(client, prompt, max_tokens, request_id)

    tasks = [
        limited_query(prompt, i + 1)
        for i, prompt in enumerate(prompts)
    ]
    results = await asyncio.gather(*tasks)
    return list(results)


# =============================================================================
# 3. エラーハンドリング（非同期版）
# =============================================================================

async def run_with_error_handling(
    client: AsyncAnthropic,
    prompts: list[str],
    max_tokens: int = 100,
    timeout: float = 30.0
) -> list[dict]:
    """
    エラーハンドリング付き並行処理

    各リクエストでエラーが発生しても他のリクエストに影響しない。
    return_exceptions=True を使うことで、例外も結果として収集できる。

    Args:
        client: 非同期Anthropicクライアント
        prompts: プロンプトのリスト
        max_tokens: 最大トークン数
        timeout: タイムアウト時間（秒）

    Returns:
        list[dict]: 各リクエストの結果（エラー情報を含む）
    """
    tasks = [
        async_query_with_timeout(
            client, prompt, max_tokens, timeout=timeout, request_id=i + 1
        )
        for i, prompt in enumerate(prompts)
    ]

    # return_exceptions=True: タスクが例外を発生させても他のタスクは続行
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 例外の場合はエラー情報に変換
    results = []
    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            results.append({
                "id": i + 1,
                "prompt": prompts[i][:40],
                "text": None,
                "elapsed": 0.0,
                "error": str(result)
            })
        else:
            results.append(result)
    return results


# =============================================================================
# 4. 実行時間測定ユーティリティ
# =============================================================================

def print_results(results: list[dict], title: str) -> None:
    """
    処理結果を表示する

    Args:
        results: 処理結果のリスト
        title: 表示タイトル
    """
    print(f"\n--- {title} ---")
    total_elapsed = 0.0
    for result in results:
        status = "✅" if result.get("text") else "❌"
        error_info = f" [{result.get('error')}]" if result.get("error") else ""
        print(f"  [{result['id']}] {status} {result['elapsed']:.3f}秒 "
              f"| {result['prompt'][:30]}...{error_info}")
        total_elapsed = max(total_elapsed, result["elapsed"])

    # 最大経過時間（並行処理では最も遅いリクエストの時間）
    print(f"  最大レスポンスタイム: {total_elapsed:.3f}秒")


# =============================================================================
# 5. メインのデモ
# =============================================================================

async def main() -> None:
    """
    非同期処理のメインデモ

    逐次処理と並行処理のパフォーマンスを比較します。
    """
    print("=" * 60)
    print("非同期処理のデモ")
    print("=" * 60)

    # テスト用のプロンプト（短い質問を5つ）
    prompts = [
        "Pythonとは？1文で答えてください。",
        "Javaとは？1文で答えてください。",
        "JavaScriptとは？1文で答えてください。",
        "Goとは？1文で答えてください。",
        "Rustとは？1文で答えてください。",
    ]

    print(f"\nテスト: {len(prompts)}個のリクエストを実行します")
    print("プロンプト:")
    for i, p in enumerate(prompts, 1):
        print(f"  [{i}] {p}")

    async_client = get_async_client()

    # --- 逐次処理 ---
    print("\n[1] 逐次処理（参考）")
    start_seq = time.time()
    seq_results = await run_sequential(async_client, prompts, max_tokens=50)
    total_seq = time.time() - start_seq
    print_results(seq_results, f"逐次処理の結果（合計: {total_seq:.3f}秒）")

    # --- 並行処理 ---
    print("\n[2] 並行処理（asyncio.gather）")
    start_con = time.time()
    con_results = await run_concurrent(async_client, prompts, max_tokens=50)
    total_con = time.time() - start_con
    print_results(con_results, f"並行処理の結果（合計: {total_con:.3f}秒）")

    # --- パフォーマンス比較 ---
    print("\n--- パフォーマンス比較 ---")
    print(f"逐次処理: {total_seq:.3f}秒")
    print(f"並行処理: {total_con:.3f}秒")
    if total_con > 0:
        speedup = total_seq / total_con
        print(f"速度改善: {speedup:.1f}倍速")
    print()

    # --- 同時実行数を制限した並行処理 ---
    print("[3] 同時実行数を制限した並行処理（最大3並行）")
    start_lim = time.time()
    lim_results = await run_concurrent_with_limit(
        async_client, prompts, max_tokens=50, max_concurrent=3
    )
    total_lim = time.time() - start_lim
    print_results(lim_results, f"制限付き並行処理の結果（合計: {total_lim:.3f}秒）")

    # --- タイムアウト付き処理 ---
    print("\n[4] タイムアウト付き処理（30秒タイムアウト）")
    timeout_results = await run_with_error_handling(
        async_client, prompts[:2], max_tokens=50, timeout=30.0
    )
    print_results(timeout_results, "タイムアウト付き処理の結果")

    # ベストプラクティス表示
    async_best_practices()

    print("\n✅ 完了！次は03_monitoring.pyに進んでください。")


def async_best_practices() -> None:
    """非同期処理のベストプラクティスを表示する"""
    print("\n--- 非同期処理のベストプラクティス ---")

    best_practices = """
【✅ 非同期処理のポイント】

1. asyncio.gather() の活用
   - 独立した複数のAPIリクエストを並行実行する
   - return_exceptions=True でエラーを握りつぶさず収集する
   - 順序が重要な場合は結果のリストインデックスを使う

2. Semaphore で同時実行数を制御する
   - レート制限を守るために同時実行数を制限する
   - asyncio.Semaphore(n) で最大n個のコルーチンのみ実行
   - async with semaphore: で自動的に取得・解放

3. asyncio.wait_for() でタイムアウト
   - 長時間実行するコルーチンに必ず設定する
   - asyncio.TimeoutError をキャッチして適切に処理する

4. Google Colab での非同期処理
   - Colab はすでにイベントループが動いている
   - nest_asyncio.apply() で asyncio.run() を使えるようにする
   - または await を直接セルで使う

5. 非同期クライアントの使い分け
   - 同期処理: Anthropic クライアント
   - 非同期処理: AsyncAnthropic クライアント
   - 混在させないこと

【⚠️ よくある間違い】
1. 非同期関数を await なしで呼び出す → コルーチンが実行されない
2. 同期クライアントを async 関数で使う → イベントループをブロック
3. 無制限に並行実行する → レート制限に引っかかる

【💡 CCA試験のポイント】
- asyncio.gather() = 並行実行
- asyncio.Semaphore = 同時実行数の制限
- asyncio.wait_for() = タイムアウト
- AsyncAnthropic = 非同期クライアント
"""
    print(best_practices)


if __name__ == "__main__":
    # Google Colab では以下のように実行する:
    # import nest_asyncio
    # nest_asyncio.apply()
    # asyncio.run(main())

    # ローカル環境での実行
    try:
        # Colab 環境では nest_asyncio を適用
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass  # ローカル環境では不要

    asyncio.run(main())
