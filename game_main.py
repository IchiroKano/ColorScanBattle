import asyncio
import datetime
import logging
import os
import sys
import time
import subprocess

import pygame

from game_ai import generate_live_commentary_async, check_ai_availability
from game_battle import BattleManager
from game_events import EventManager
from game_player import PlayerManager
from game_stage import draw_battle, StageRenderer
from game_ui import get_fonts, draw_status, draw_ai_status
from game_utils import music_files, log_to_file, initialize_log_file, load_sounds, prompt_to_file
# max_turn を game_utils からインポート
from game_utils import max_turn
# default_volume を game_utils に統合
from game_utils import default_volume

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

battle_log = []           # 戦闘ログを追記するリスト

# 実況コメントを保持する変数
live_commentary = ""
ai_session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 起動時に一度だけセッションIDを生成
logger.info(f"セッションID: {ai_session_id}")

class GameState:
    def __init__(self):
        self.stage = "staging"
        self.turn = 1
        self.step = 1
        self.hp1 = 100
        self.hp2 = 100
        self.player1_status = {}
        self.player2_status = {}
        self.battle_log = []
        self.action1 = ""
        self.action2 = ""
        self.step_timer = 0
        self.jump_start_frame1 = None
        self.jump_start_frame2 = None
        self.turn_updated = False  # ターン更新フラグ（AI実況用）

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
        self.turn_updated = True  # ターンが更新されたことを記録

        # ターミナルログにセパレーターを表示
        logger.info("\n" + "=" * 40 + f" ターン {self.turn} 開始 " + "=" * 40 + "\n")

    def is_battle_over(self):
        return self.turn > 7 or self.hp1 <= 0 or self.hp2 <= 0

# プレイヤーの初期HPを計算する関数を修正
def calculate_initial_hp(base_hp):
    calculated_hp = max(50, min(100, 50 + base_hp))  # 50以上100以下に制限
    return calculated_hp

# 音量を設定する関数を追加
def set_volume(volume):
    try:
        # 音量を設定する処理（例: pygame.mixerを使用する場合）
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.set_volume(volume)
        print(f"音量を{volume * 100:.0f}%に設定しました。")
    except Exception as e:
        print(f"音量設定中にエラーが発生しました: {e}")

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

# 初期化時に音量を設定
set_volume(default_volume)

# インスタンスの初期化
game_state = GameState()
player_manager = PlayerManager()
event_manager = EventManager(player_manager)  # EventManager のインスタンスを作成
stage_renderer = StageRenderer()  # StageRenderer のインスタンスを作成
battle_manager = None

# アプリ起動時にJSONを読み込まない。ステージング画面で［リロード］ボタンを押したらJSONを読み込むゲームのため。
#player_manager.load_player("player1")
#player_manager.load_player("player2")

# player_data参照時にデフォルト値を設定
def get_player_name(player_key):
    return player_manager.player_data.get(player_key, {}).get("キャラ名", "Unknown")

sounds = load_sounds()    # 効果音をロード
initialize_log_file()     # ログファイルを初期化（空にする）

clock = pygame.time.Clock()  # フレームレート制御用のClockオブジェクトを作成

# 起動時の音を再生
try:
    pygame.mixer.music.load(music_files['startup'])
    pygame.mixer.music.set_volume(default_volume)  # 音量を設定
    pygame.mixer.music.play()
except pygame.error as e:
    print(f"起動時の音再生中にエラーが発生しました: {e}")

# 実況コメント生成の回数を確認するためのカウンタを追加
generate_commentary_count = 0

# 実況コメント生成の呼び出しをターン更新時に限定する
async def update_live_commentary_if_needed():
    global live_commentary, generate_commentary_count
    if game_state.turn_updated:  # ターン更新時のみ実況コメントを生成
        try:
            generate_commentary_count += 1  # 呼び出し回数をカウント
            logger.info(f"-----------------------------\n実況コメント生成の呼び出し回数: {generate_commentary_count}")

            # 差分プロンプトを作成（各ターン更新時に最小限の情報）
            name1 = get_player_name("player1")
            name2 = get_player_name("player2")
            a1 = battle_manager.action1 if battle_manager and battle_manager.action1 else "待機"
            a2 = battle_manager.action2 if battle_manager and battle_manager.action2 else "待機"
            hp1 = battle_manager.hp1 if battle_manager else 100
            hp2 = battle_manager.hp2 if battle_manager else 100
            turn_label = max(1, (battle_manager.turn - 1) if battle_manager else 1)
            # 実況AI生成★
            delta_text = (
                f"■ターン{turn_label}: Player1の行動={a1}, 残HP={hp1}; Player2の行動={a2}, 残HP={hp2}."
            )

            if turn_label == 1:
                # 選手情報をdelta_textの先頭に追加
                player_info = player_manager.player_parameters
                delta_text = f"{player_info}\n{delta_text}"  # 選手情報を追加

            # 実況コメント生成の呼び出し時刻を記録
            start_time = datetime.datetime.now()
            logger.info(f"実況コメント生成の呼び出し時刻: {start_time}")

            try:
                live_commentary = await generate_live_commentary_async(player_manager, ai_session_id, delta_text)
                end_time = datetime.datetime.now()
                logger.info("実況コメント生成成功")

                # 実況コメント生成スピードを計算
                time_diff = (end_time - start_time).total_seconds()
                log_to_file(f"実況コメント生成スピード：{time_diff:.2f}秒")

            except Exception as e:
                logger.error("実況コメント生成中にエラーが発生しました: %s", e)

            # ターン更新フラグをリセット
            game_state.turn_updated = False
        except Exception as e:
            logger.error("実況コメント生成中にエラーが発生しました: %s", e)

# メインループの冒頭でAI利用可否を確認
import time

def display_loading_message():
    draw_ai_status(screen, "Loading ...", width, height)
    pygame.display.update()

# "Loading ..."を表示
if game_state.stage == "staging":
    display_loading_message()
    time.sleep(0)  # 1秒待機

# AIサーバーの可用性を確認してログに出力
ai_accessible = check_ai_availability()
print(f"AIサーバー利用可否: {'利用可能' if ai_accessible else '利用不可'}")

# update_live_commentaryの呼び出し箇所にログを追加
# 実況コメント生成タスクの状態を管理するフラグを追加
commentary_task_running = False

# 実況コメント生成タスクを管理する変数を追加
commentary_task = None

# 非同期で実況コメントを取得する関数を修正
def log_update_live_commentary():
    """実況コメント生成のログを更新する関数"""
    try:
        asyncio.run(update_live_commentary_if_needed())  # asyncio.run() を使用して非同期関数を実行
    except Exception as e:
        logging.error(f"実況コメント生成中にエラーが発生しました: {e}")

# 実況コメント生成タスクの完了確認を修正
def check_commentary_task():
    global commentary_task, live_commentary
    if commentary_task and commentary_task.done():
        try:
            live_commentary = commentary_task.result()
        except Exception as e:
            logger.error(f"実況コメント生成タスクのエラー: {e}")
        finally:
            commentary_task = None

# draw_battle関数内で実況コメントをログに出力する箇所を修正
def log_draw_battle_commentary(commentary):
    # 重複ログを防ぐために、前回のコメントと異なる場合のみ出力
    if not hasattr(log_draw_battle_commentary, "previous_commentary"):
        log_draw_battle_commentary.previous_commentary = None

    if commentary != log_draw_battle_commentary.previous_commentary:
        print(f"生成された実況コメント（★）：<-- {commentary} -->")
        log_draw_battle_commentary.previous_commentary = commentary

# -----------------------------------------------------------
# メインループ
# -----------------------------------------------------------
async def main_loop():
    global battle_manager
    summary = ""  # 総評の初期化
    frame_count = 0  # 各ターンの描画回数をカウント
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
            pygame.mixer.music.set_volume(default_volume)  # 音量を設定
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
                pygame.mixer.music.set_volume(default_volume)  # 音量を設定
                pygame.mixer.music.play()
                player_manager.load_player("player1")

            # ボタン［プレイヤー２の読み込み］
            elif result == "reload2":
                pygame.mixer.music.stop()
                pygame.mixer.music.load(music_files['reload2'])
                pygame.mixer.music.set_volume(default_volume)  # 音量を設定
                pygame.mixer.music.play()
                player_manager.load_player("player2")

            # ボタン［戦闘スタート］
            elif result == "start":
                game_state.stage = "battle"
                battle_manager = BattleManager(player_manager.player_data)

        # 【ステップ２】戦闘中の画面：
        if game_state.stage == "battle" and battle_manager:
            frame_count += 1  # 描画回数をインクリメント

            game_state.stage = battle_manager.advance_step(now, game_state)  # advance_step メソッドをインスタンス経由で呼び出し

            # draw_battle関数に必要な引数を渡す
            draw_battle(
                screen,
                font,
                big_font,
                log_font,
                width,
                height,
                game_state.turn,
                game_state.step,
                game_state.hp1,
                game_state.hp2,
                player_manager.player_images,
                battle_manager.action1,
                battle_manager.action2,
                game_state.battle_log,
                pygame.time.get_ticks(),
                game_state.jump_start_frame1,
                game_state.jump_start_frame2,
                live_commentary,
                game_state.player1_status,
                game_state.player2_status,
                player_manager.player_data
            )

            # プレイヤーのエフェクト中に実況コメントを生成（非同期タスクをバックグラウンドで実行）
            await update_live_commentary_if_needed()  # 非同期関数をawaitで呼び出す

            # エフェクト処理（例: 2秒間のエフェクト）
            effect_start_time = pygame.time.get_ticks()
            while pygame.time.get_ticks() - effect_start_time < 2000:
                draw_battle(
                    screen, font, big_font, log_font, width, height,
                    battle_manager.turn, battle_manager.step, battle_manager.hp1, battle_manager.hp2,
                    player_manager.player_images, battle_manager.action1, battle_manager.action2,
                    battle_manager.battle_log, pygame.time.get_ticks(),
                    battle_manager.jump_start_frame1, battle_manager.jump_start_frame2,
                    live_commentary,
                    game_state.player1_status,
                    game_state.player2_status,
                    player_manager.player_data
                )
                log_draw_battle_commentary(live_commentary)  # ログ追加
                pygame.display.update()
                clock.tick(30)

            # エフェクト描画
            draw_battle(
                screen, font, big_font, log_font, width, height,
                battle_manager.turn, battle_manager.step, battle_manager.hp1, battle_manager.hp2,
                player_manager.player_images, battle_manager.action1, battle_manager.action2,
                battle_manager.battle_log, pygame.time.get_ticks(),
                battle_manager.jump_start_frame1, battle_manager.jump_start_frame2,
                live_commentary,
                game_state.player1_status,
                game_state.player2_status,
                player_manager.player_data
            )

            # 戦闘終了判定をエフェクト描画後に移動
            if battle_manager.is_battle_over():
                log_to_file(f"ターン{battle_manager.turn}の描画回数: {frame_count}")  # 描画回数をログに記録
                game_state.stage = "result"
                log_to_file("戦闘終了")
                # ここで総評をAIで生成してsummaryに格納する処理を追加可能
                delta_text = f"■総評: ターン１からここまでの対戦の特長を、熱血口調で簡潔に述べよ"
                prompt_to_file('入力<-- ' + delta_text + ' -->')
                summary = await generate_live_commentary_async(player_manager, ai_session_id, delta_text, is_summary=True)

                pygame.mixer.music.load(music_files['stage_final'])
                pygame.mixer.music.set_volume(default_volume)  # 音量を設定
                pygame.mixer.music.play()

            # 実況コメント生成タスクの完了を確認
            check_commentary_task()

            # ターン更新時に実況コメント生成を呼び出し
            await update_live_commentary_if_needed()

            # draw_battle関数に必要な引数を渡す
            draw_battle(
                screen,
                font,
                big_font,
                log_font,
                width,
                height,
                game_state.turn,
                game_state.step,
                game_state.hp1,
                game_state.hp2,
                player_manager.player_images,
                battle_manager.action1,
                battle_manager.action2,
                game_state.battle_log,
                pygame.time.get_ticks(),
                game_state.jump_start_frame1,
                game_state.jump_start_frame2,
                live_commentary,
                game_state.player1_status,
                game_state.player2_status,
                player_manager.player_data
            )

            # 戦闘ステップの描画
            draw_battle(
                screen, font, big_font, log_font, width, height,
                battle_manager.turn, battle_manager.step, battle_manager.hp1, battle_manager.hp2,
                player_manager.player_images, battle_manager.action1, battle_manager.action2,
                battle_manager.battle_log, pygame.time.get_ticks(),
                battle_manager.jump_start_frame1, battle_manager.jump_start_frame2,
                live_commentary,
                game_state.player1_status,
                game_state.player2_status,
                player_manager.player_data
            )

            # 戦闘ステップの効果音を再生
            if battle_manager.action1 == "attack" or battle_manager.action2 == "attack":
                sounds['attack'].play()
            elif battle_manager.action1 == "healing" or battle_manager.action2 == "healing":
                sounds['healing'].play()
            elif battle_manager.action1 == "magic" or battle_manager.action2 == "magic":
                sounds['magic'].play()

            # ターン開始時にのみステータスをログに出力
            if game_state.turn_updated:
                print("Player 1 Status:", player_manager.player_data["player1"])
                print("Player 2 Status:", player_manager.player_data["player2"])
                game_state.turn_updated = False  # フラグをリセット

        # 【ステップ３】対戦結果の表示：［再起動］ボタンが押されるまで
        elif game_state.stage == "result":
            buttons = stage_renderer.draw_result(screen, font, big_font, battle_manager.hp1, battle_manager.hp2, width, height,
                                                 player_manager.player_images, battle_manager.action1, battle_manager.action2,
                                                 battle_manager.battle_log, now, None, None, None, summary)
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


        pygame.display.update()
        clock.tick(30)

# main_loop の呼び出し
if __name__ == "__main__":
    asyncio.run(main_loop())  # メインループを非同期で実行




