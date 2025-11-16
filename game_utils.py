#--------------------------------
# 共通関数はこのファイルに記載する
#--------------------------------
import pygame

# default_volume を統一
# 音量のデフォルト値
default_volume = 0.1

# 最大ターン数
max_turn = 3


# ログファイルを初期化する関数
def initialize_log_file():
    """ログファイルを初期化する"""
    with open("battle_log.txt", "w", encoding="utf-8") as f:
        f.write("")  # battle_log.txt を空にする
    with open("input_prompt.txt", "w", encoding="utf-8") as f:
        f.write("")  # input_prompt.txt を空にする

# JSONパラメータをゲーム内パラメータに補正 基準50+補正(JSON値の0.5倍)
def convert_param(value):
    try:
        return int(50 + float(value) * 0.5)
    except Exception as e:
        print("[ERROR] convert_param failed:", value, e)
        return 50

# ログメッセージをファイルに書き込む関数
def log_to_file(message):
    """
    ログメッセージをファイルに書き込む
    """
    with open("battle_log.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")

# 入力プロンプトをファイルに書き込む関数
def prompt_to_file(message):
    """
    入力プロンプトをファイルに書き込む
    """
    with open("input_prompt.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")


# 音楽ファイルの一元管理
music_files = {
    'reload1': "music/stage_left.wav",
    'reload2': "music/stage_right.wav",
    'fight_op': "music/fight_op.wav",
    'stage_base': "music/stage_base.wav",
    'startup': "music/stage_base.wav",
    'stage_final': "music/stage_final.wav"
}

# 効果音のロードを一元管理
def load_sounds():
    pygame.mixer.init()
    return {
        'attack': pygame.mixer.Sound("music/fight_attack.wav"),
        'magic': pygame.mixer.Sound("music/fight_magic.wav"),
        'healing': pygame.mixer.Sound("music/fight_healing.wav"),
        'defence': pygame.mixer.Sound("music/fight_defence.wav"),
        'jump': pygame.mixer.Sound("music/fight_jump.wav")
    }


