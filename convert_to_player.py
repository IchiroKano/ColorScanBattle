import json
import random

# 色系統の分類
color_family = {
    "Red1": "red",
    "Red2": "red",
    "Orange": "yellow",
    "Pink": "yellow",
    "Yellow": "yellow",
    "Green": "green",
    "LightGreen": "green",
    "Cyan": "blue",
    "Blue": "blue",
    "Purple": "blue",
    "Gray": "white",
    "White": "white"
}

# 色→パラメータのマッピング
color_to_param = {
    "Red1": "攻撃力",
    "Red2": "攻撃力",
    "Orange": "防御力",
    "Yellow": "すばやさ",
    "Green": "回復力",
    "LightGreen": "回復力",
    "Cyan": "回避力",
    "Blue": "回避力",
    "Pink": "すばやさ",
    "Purple": "回避力",
    "Gray": "体力",
    "White": "体力"
}

# 色系統ごとのキャラ名リスト（10個ずつ）
character_names = {
    "red": ["バーニング・レイジ", "クリムゾン・ブレード", "フレイム・ハウラー", "スカーレット・ファング", "レッド・ストーム", "ブラッド・スナイパー", "マグマ・クラッシャー", "ラヴァ・スプリンター", "インフェルノ・ナイト", "ブレイズ・ファイター"],
    "blue": ["アクア・ミラージュ", "ブルー・シャドウ", "アイス・スナイパー", "ネビュラ・ウィザード", "ディープ・フロー", "サイレント・ウェイブ", "フロスト・ランサー", "ミスティ・スピア", "ブルー・フェンサー", "スプラッシュ・アーチャー"],
    "green": ["リーフ・セージ", "グリーン・ヒーラー", "フォレスト・ガード", "ハーブ・メイジ", "ナチュラル・スピリット", "エコー・ドリュイド", "ブリーズ・プリースト", "ヴァイン・シールド", "グラス・ウォーカー", "セントラル・スプライト"],
    "yellow": ["ライトニング・スニーク", "イエロー・フラッシュ", "スピード・スター", "シャイニング・スカウト", "ゴールド・トリックスター", "サンダー・ダンサー", "ラピッド・ブレード", "スパーク・レンジャー", "フリッカー・フェンサー", "イエロー・スプリンター"],
    "white": ["ホーリー・ガーディアン", "ホワイト・ウォール", "セラフィム・ナイト", "ブレッシング・パラディン", "ピュア・シールド", "ライト・ウォッチャー", "グレース・タンク", "ルミナス・ウォリアー", "ディヴァイン・バリア", "ホープ・セントリー"]
}

# 色系統ごとのスキルリスト（3つ以上）
skills_by_family = {
    "red": ["フレイムスラッシュ", "バーサークモード", "血気覚醒", "マグマパンチ", "烈火の剣"],
    "blue": ["ウォーターヴェイル", "幻影分身", "氷結の矢", "深海の波動", "ブルーシールド"],
    "green": ["ヒールブレス", "精霊の加護", "リジェネレーション", "自然の癒し", "フォレストバリア"],
    "yellow": ["電光石火", "スピードトラップ", "影走り", "閃光の突撃", "加速の陣"],
    "white": ["聖盾の守護", "鉄壁の構え", "リフレクトバリア", "光の祈り", "守護の結界"]
}

# 色系統ごとの画像ファイルリスト
image_files = {
    "red":    [f"red1-{i}.png" for i in range(1, 6)],
    "blue":   [f"blue1-{i}.png" for i in range(1, 6)],
    "green":  [f"green1-{i}.png" for i in range(1, 6)],
    "yellow": [f"yellow1-{i}.png" for i in range(1, 6)],
    "white":  [f"white1-{i}.png" for i in range(1, 6)]
}

def convert_color_to_player(color_json_path="color_map.json", output_path="player_spec.json"):
    # 色データ読み込み
    with open(color_json_path, "r", encoding="utf-8") as f:
        color_data = json.load(f)

    # 色系統の決定
    dominant_color = max(color_data, key=color_data.get)
    dominant_family = color_family.get(dominant_color, "unknown")

    # パラメータ初期化と計算
    player_params = {
        "攻撃力": 0.0, "防御力": 0.0, "すばやさ": 0.0,
        "回復力": 0.0, "体力": 0.0, "回避力": 0.0
    }

    for color, value in color_data.items():
        param = color_to_param.get(color)
        if param:
            player_params[param] += value

    # スケーリング
    total = sum(player_params.values())
    scale = 100 / total if total > 0 else 0
    for key in player_params:
        player_params[key] = round(player_params[key] * scale, 1)

    # キャラ情報追加
    player_params["色系統"] = dominant_family
    player_params["キャラ名"] = random.choice(character_names[dominant_family])
    player_params["スキルセット"] = {
        "skill1": random.choice(skills_by_family[dominant_family]),
        "skill2": random.choice(skills_by_family[dominant_family]),
        "skill3": random.choice(skills_by_family[dominant_family])
    }
    player_params["画像ファイル"] = random.choice(image_files[dominant_family])

    # JSON出力
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(player_params, f, ensure_ascii=False, indent=2)

    print(f"{output_path} に出力しました。キャラ:", player_params["キャラ名"])
    return player_params
