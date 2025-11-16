import requests

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

if __name__ == "__main__":
    result = check_ai_availability()
    print(f"AI利用可能: {result}")