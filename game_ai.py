# ollamaが動くWSL Ubuntu環境でポート転送を起動しておくこと
# $ socat TCP-LISTEN:11435,fork TCP:127.0.0.1:11434
# 検査は、Windows> curl http://localhost:11435
# 期待する応答は、Ollama is running

import requests
import asyncio

# APIエンドポイント（WSLでsocat経由なら11435）
url = "http://localhost:11435/api/generate"

# パラメーター定義
ai_model = "granite3.3:2b"
# ai_model = "granite4:350m-h"

input_prompt = """
・あなたは熱狂的な実況アナウンサーです。
・２人のプレイヤーの対戦ゲームです。
・promptのログを元にして、ゲームの展開を臨場感たっぷりに実況してください。
・キャラクター名やスキル名を活かし、状況をわかりやすく。
・100文字以内で伝えてください。
・ステージング（ロード完了）のパラメーターは表示しない。

---------------------------　テンプレート例　-------------------------------
(P1) キャラ名1 は P1の行動 をした。info1 したためダメージはｘｘ。
(P2) キャラ名2 は P2の行動 をした。info2 したためダメージはｘｘ。

--------------------------- プレイヤーの属性 -------------------------------
"""

# player_parameters変数を定義し、プレイヤー情報を追加する関数
def add_player_parameters(param_str):
    global player_parameters  # グローバル変数として定義
    player_parameters = ""  # 初期化
    player_parameters += param_str + "\n"

# グローバル変数でAIアクセスの状態を管理
ai_accessible = True

# 非同期で実況コメントを生成する関数
async def generate_live_commentary_async():
    global ai_accessible

    if not ai_accessible:
        return "No AI"

    payload = {
        "model": ai_model,
        "prompt": input_prompt + player_parameters,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 100
    }

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload))

        if response.status_code == 200:
            data = response.json()
            return data["response"]
        else:
            print(f"❌ エラー: {response.status_code}")
            print(response.text)
            return "No AI"
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        ai_accessible = False  # 次回以降のアクセスをスキップ
        return "No AI"

# 同期的に実況コメントを生成するラッパー関数
def generate_live_commentary():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(generate_live_commentary_async())
