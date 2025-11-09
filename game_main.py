import pygame, sys
from game_ui import get_fonts, draw_status
from game_events import EventManager
from game_stage import draw_battle, StageRenderer
from game_battle import BattleManager
from game_utils import music_files, log_to_file, initialize_log_file
from game_player import PlayerManager
import os
import subprocess
from game_utils import load_sounds
from game_ai import generate_live_commentary_async
import asyncio

battle_log = []           # 戦闘ログを追記するリスト

# 実況コメントを保持する変数
live_commentary = ""

class GameState:
    def __init__(self):
        self.stage = "staging"
        self.turn = 1
        self.step = 1
        self.hp1 = 100
        self.hp2 = 100
        self.battle_log = []
        self.action1 = ""
        self.action2 = ""
        self.step_timer = 0
        self.jump_start_frame1 = None
        self.jump_start_frame2 = None

    def reset(self):
        self.__init__()

    def start_battle(self, now):
        self.stage = "battle"
        self.turn = 1
        self.step = 1
        self.hp1 = 100
        self.hp2 = 100
        self.battle_log = []
        self.step_timer = now

    def end_battle(self):
        self.stage = "result"

    def update_turn(self):
        self.turn += 1
        self.step = 1

    def is_battle_over(self):
        return self.turn > 7 or self.hp1 <= 0 or self.hp2 <= 0

# プレイヤーの初期HPを計算する関数を修正
def calculate_initial_hp(base_hp):
    calculated_hp = max(50, min(100, 50 + base_hp))  # 50以上100以下に制限
    return calculated_hp

# Windows の ウィンドウを生成する
pygame.init()
# pygame.mixer.init()の引数を明示的に指定
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
info = pygame.display.Info()                                          # ディスプレイ解像度を取得
width, height = info.current_w, info.current_h                        # フルスクリーン用に画面サイズを設定
screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)  # フルスクリーン
font, bold_font, log_font, big_font = get_fonts(height)               # フォント取得

# ウィンドウタイトルを設定
pygame.display.set_caption("Game Window")

# 必要に応じてウィンドウアイコンを設定（例: img/char-blue.png を使用）
icon = pygame.image.load("img/char-blue.png")
pygame.display.set_icon(icon)

# インスタンスの初期化
game_state = GameState()
player_manager = PlayerManager()
event_manager = EventManager(player_manager)  # EventManager のインスタンスを作成
stage_renderer = StageRenderer()  # StageRenderer のインスタンスを作成
battle_manager = None

sounds = load_sounds()    # 効果音をロード
initialize_log_file()     # ログファイルを初期化（空にする）

clock = pygame.time.Clock()  # フレームレート制御用のClockオブジェクトを作成

# 起動時の音を再生
try:
    pygame.mixer.music.load(music_files['startup'])
    pygame.mixer.music.play()
    #while pygame.mixer.music.get_busy():
    #    pygame.time.wait(100)
except pygame.error as e:
    print(f"起動時の音再生中にエラーが発生しました: {e}")

# 非同期で実況コメントを取得する関数を呼び出す
async def update_live_commentary():
    global live_commentary
    live_commentary = await generate_live_commentary_async()

# -----------------------------------------------------------
# メインループ
# -----------------------------------------------------------
while True:
    screen.fill((240, 240, 240))
    now = pygame.time.get_ticks()

    # イベントを一度だけ取得
    events = pygame.event.get()

    # イベント処理
    buttons = stage_renderer.draw_staging(screen, font, bold_font, player_manager.player_data, player_manager.player_images, width, height) if game_state.stage == "staging" else {}
    result = event_manager.handle_events(game_state.stage, buttons, player_manager.player_data, player_manager.player_images, player_manager.eyecatch_images, now, events)

    # ゲーム終了[ESC]キー
    if result == "quit":
        pygame.quit()
        os._exit(0)  # プロセスを強制終了

    # ステージング画面の［対戦］スタートボタンが押されたとき
    elif result == "start":
        game_state.stage = "battle"
        pygame.mixer.music.stop()  # 現在の音楽を停止
        pygame.mixer.music.load(music_files['fight_op'])
        pygame.mixer.music.play()
        if not battle_manager:  # BattleManagerが未生成の場合のみ生成
            battle_manager = BattleManager(player_manager.player_data)

    # 対戦結果を表示した画面の［再スタート］ボタン
    elif result == "restart":
        game_state.reset()
        player_manager.load_player("player1")
        player_manager.load_player("player2")

    # 【ステップ１】ステージング：［プレイヤー1,2］のJSON読み込みボタン
    elif game_state.stage == "staging":
        game_state.reset()  # ステージング画面に入るたびに変数を初期化
        buttons = stage_renderer.draw_staging(screen, font, bold_font, player_manager.player_data, player_manager.player_images, width, height)
        result = event_manager.handle_events(game_state.stage, buttons, player_manager.player_data, player_manager.player_images, player_manager.eyecatch_images, now, events)

        # ボタン［プレイヤー１の読み込み］
        if result == "reload1":
            pygame.mixer.music.stop()  # 音楽再生の前に現在の音楽を停止
            pygame.mixer.music.load(music_files['reload1'])
            pygame.mixer.music.play()
            player_manager.load_player("player1")

        # ボタン［プレイヤー２の読み込み］
        elif result == "reload2":
            pygame.mixer.music.stop()
            pygame.mixer.music.load(music_files['reload2'])
            pygame.mixer.music.play()
            player_manager.load_player("player2")

        # ボタン［戦闘スタート］
        elif result == "start":
            game_state.stage = "battle"
            battle_manager = BattleManager(player_manager.player_data)

    # 【ステップ２】戦闘中の画面：
    if game_state.stage == "battle" and battle_manager:
        game_state.stage = battle_manager.advance_step(now)  # advance_step メソッドをインスタンス経由で呼び出し

        # 各ターンで実況コメントを非同期に更新
        asyncio.run(update_live_commentary())

        # 戦闘終了判定
        if battle_manager.is_battle_over():
            game_state.stage = "result"
            log_to_file("戦闘終了")
            pygame.mixer.music.load(music_files['stage_final'])
            pygame.mixer.music.play()

        # 戦闘ステップの描画
        draw_battle(
            screen, font, big_font, log_font, width, height,
            battle_manager.turn, battle_manager.step, battle_manager.hp1, battle_manager.hp2,
            player_manager.player_images, battle_manager.action1, battle_manager.action2,
            battle_manager.battle_log, pygame.time.get_ticks(),
            battle_manager.jump_start_frame1, battle_manager.jump_start_frame2,
            live_commentary  # 実況コメントを渡す
        )

        # 戦闘ステップの効果音を再生
        if battle_manager.action1 == "attack" or battle_manager.action2 == "attack":
            sounds['attack'].play()
        elif battle_manager.action1 == "healing" or battle_manager.action2 == "healing":
            sounds['healing'].play()
        elif battle_manager.action1 == "magic" or battle_manager.action2 == "magic":
            sounds['magic'].play()

        # ステータスを画面端に表示
        draw_status(screen, player_manager.player_data["player1"], player_manager.player_data["player2"])

    # 【ステップ３】対戦結果の表示：［再起動］ボタンが押されるまで
    elif game_state.stage == "result":
        buttons = stage_renderer.draw_result(screen, font, big_font, battle_manager.hp1, battle_manager.hp2, width, height,
                                             player_manager.player_images, battle_manager.action1, battle_manager.action2,
                                             battle_manager.battle_log, now, None, None, None)
        result = event_manager.handle_events(game_state.stage, buttons, player_manager.player_data, player_manager.player_images, player_manager.eyecatch_images, now, events)

        # 再起動ボタンが押されたらゲームをリセット
        if result == "restart":
            game_state.reset()
            player_manager.load_player("player1")
            player_manager.load_player("player2")
            game_state.stage = "staging"

        # 再起動ボタンが押されたらプログラムを再起動
        elif result == "next":
            pygame.quit()
            subprocess.Popen([sys.executable, *sys.argv])
            os._exit(0)  # プロセスを強制終了

        # ステータスを画面端に表示
        draw_status(screen, player_manager.player_data["player1"], player_manager.player_data["player2"])

    pygame.display.update()
    clock.tick(30)



