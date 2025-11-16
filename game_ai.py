# ollamaが動くWSL Ubuntu環境でポート転送を起動しておくこと
# $ socat TCP-LISTEN:11435,fork TCP:127.0.0.1:11434
# 検査は、Windows> curl http://localhost:11435
# 期待する応答は、Ollama is running

# Organized imports
import asyncio
import requests
from game_player import PlayerManager
from game_utils import prompt_to_file

def check_ai_availability():
    """
    AIの利用可否を確認する関数。
    Returns:
        bool: AIが利用可能な場合はTrue、利用不可の場合はFalse。
    """
    url = "http://razpi00.local:11434/api/tags"
    try:
        response = requests.get(url, timeout=5)
        print(f"AI利用可否確認: ステータスコード={response.status_code}")  # ステータスコードを出力
        print(f"レスポンス内容: {response.text}")  # レスポンス内容を出力
        if response.status_code == 200:
            return True
        else:
            print(f"AI利用不可: ステータスコード {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"AI利用不可: {e}")  # 例外内容を出力
        return False

# 動作確認済み（合格）
#import requests
#url = "http://razpi00.local:11434/api/generate"
#payload = {
#    "model": "granite4:350m-h",
#    "prompt": "こんにちは",
#    "stream": False
#}
#response = requests.post(url, json=payload)
#print(response.json()["response"])

# Ollama: APIエンドポイント（From Windows to ラズパイ4）
#url = "http://razpi00.local:11434/api/generate"

# LangFlow: API エンドポイント（From Windows to ラズパイ4）
url = "http://razpi00.local:7860/api/v1/run/06dce709-8745-4275-a63e-e5a64c976e74"
api_key = "sk-ySAlois_p3dpXTPP6B6h8SiUCGTsJKEHgRB-W4GwnGU"

# パラメーター定義
# ai_model = "granite3.3:2b"
ai_model = "granite4:350m-h"

input_prompt = ""  # LangFlow使うときは空白にする。LangFlow側でプロンプトを設定するため。

# グローバル変数でAIアクセスの状態を管理
ai_accessible = True
initialized_sessions = set()  # session_id ごとに初回フル送信済みかを記録

# 返却JSONからテキストを安全に抽出するユーティリティ
def _extract_ai_text(data):
    """LangFlow/Ollama/汎用的なレスポンスからテキストを取り出す。
    代表的なキー: response, text, message, content, output, result
    または outputs の深い入れ子構造。
    """
    if data is None:
        return None

    # 代表キーを優先的にチェック
    if isinstance(data, dict):
        for k in ("response", "text", "message", "content", "output", "result"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v

    # 深い入れ子の構造を探索（DFS）
    def _dfs(obj):
        if isinstance(obj, dict):
            # 代表キーを優先
            for k in ("response", "text", "message", "content", "output", "result"):
                if k in obj and isinstance(obj[k], str) and obj[k].strip():
                    return obj[k]
            # 値を辿る
            for v in obj.values():
                res = _dfs(v)
                if isinstance(res, str) and res.strip():
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = _dfs(item)
                if isinstance(res, str) and res.strip():
                    return res
        return None

    return _dfs(data)

# 非同期で実況コメントを生成する関数
async def generate_live_commentary_async(pm: PlayerManager, session_id: str | None = None, delta_text: str | None = None, is_summary: bool = False):
    """
    AIを使用して実況コメントまたは総評を生成する非同期関数。
    :param pm: PlayerManagerインスタンス。
    :param session_id: セッションID。
    :param delta_text: 差分テキスト（実況コメント用）。
    :param is_summary: 総評生成フラグ。
    """
    global ai_accessible

    if not ai_accessible:
        return "AIサーバーが利用できないため、コメントは表示されません。"

    if not pm.player_parameters:
        return "No Player Data (準備中)"

    if is_summary:
        prompt = f"■総評：この対戦がどんな特長のあるバトルだったのか、要点のみ短く述べてください。"
    else:
        prompt = delta_text or "前ターンの差分情報がありません。要点のみ短く実況してください。"

    payload = {
        "prompt": prompt,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 150 if is_summary else 100
    }

    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["x-api-key"] = api_key

    try:
        # promptを input_prompt.txt にログ出力
        prompt_to_file(prompt)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, headers=headers))

        if response.status_code == 200:
            # レスポンスからテキストを抽出
            data = response.json()
            text = _extract_ai_text(data)
            if isinstance(text, str) and text.strip():
                prompt_to_file('出力<-- ' + text + ' -->')  # AI応答をログ出力
                return text
            else:
                return "AI format error"
        else:
            return f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        ai_accessible = False
        return "AIサーバーにリクエスト失敗"
