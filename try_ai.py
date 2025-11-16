# この構成は動いた（2025/11/11）
# カメラ　－　デスクトップPC　－有線LAN－　ラズパイ４(granite4)
#              ┗ "http://razpi00.local:11434/api/generate"
import requests

print("AIが実況コメントを生成中です...")

input_prompt = """
・あなたは熱狂的な実況アナウンサーです。
・２人のプレイヤーの対戦ゲームです。
・promptのログを元にして、ゲームの展開を臨場感たっぷりに実況してください。
・キャラクター名やスキル名を活かし、状況をわかりやすく。
・80文字以内で伝えてください。
・ステージング（ロード完了）のパラメーターは表示しない。

---------------------------　テンプレート例　-------------------------------
(P1) {キャラ名1} は {P1の行動} 、ダメージはｘｘ。
(P2) {キャラ名2} は {P2の行動} 、ダメージはｘｘ。

--------------------------- 対戦ログ -------------------------------
"""

#url = "http://razpi00.local:11434/api/generate"
url = "http://localhost:11434/api/generate"

# 外部ファイルbattle_log.txtを読み込む
with open("battle_log.txt", "r", encoding="utf-8") as file:
    battle_log_content = file.read()

payload = {
    "model": "granite4:350m-h",
    "prompt": battle_log_content,  # 外部ファイルの内容を使用
    "stream": False
}

headers = {
    "Content-Type": "application/json; charset=utf-8"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json()["response"])
