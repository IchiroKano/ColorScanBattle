#--------------------------------
# 共通関数はこのファイルに記載する
#--------------------------------

import pygame

# ログファイルを初期化する関数
def initialize_log_file():
    with open("battle_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write("ログファイルを初期化しました。\n")

# ログをファイルに出力する関数
def log_to_file(log_message):
    with open("battle_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_message + "\n")

# JSONパラメータをゲーム内パラメータに補正 基準50+補正(JSON値の0.5倍)
def convert_param(value):
    try:
        return int(50 + float(value) * 0.5)
    except Exception as e:
        print("[ERROR] convert_param failed:", value, e)
        return 50

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

