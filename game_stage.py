import pygame
from game_ui import draw_button, draw_hp_bar, draw_step_label, draw_message_label, draw_status
from game_player import draw_player_info, PlayerManager
from game_effects import draw_attack_effect, draw_magic_effect, get_anim_offset, draw_defense_effect, draw_heal_effect, draw_jump_effect, draw_sparkle_effect
# default_volume を定義
from game_utils import default_volume

# 戦闘およびステージング画面の描画クラス
class StageRenderer:
    def __init__(self):
        pass

    # ステージングステップの描画
    def draw_staging(self, screen, font, bold_font, player_data, player_images, width, height):
        if player_data.get("player1") and player_images.get("player1"):
            draw_player_info(screen, font, bold_font, player_data["player1"], player_images["player1"], int(width * 0.1), width, height)
        if player_data.get("player2") and player_images.get("player2"):
            draw_player_info(screen, font, bold_font, player_data["player2"], player_images["player2"], int(width * 0.6), width, height)

        btn_w = int(width * 0.15)
        btn_h = int(height * 0.05)
        buttons = {
            "reload1": draw_button(screen, font, "リロード1", int(width * 0.2), int(height * 0.85), btn_w, btn_h),
            "reload2": draw_button(screen, font, "リロード2", int(width * 0.8 - btn_w), int(height * 0.85), btn_w, btn_h),
            "quit": draw_button(screen, font, "終了", width - btn_w - 10, 10, btn_w, btn_h),
        }
        if player_data.get("player1") and player_data.get("player2"):
            buttons["start"] = draw_button(screen, font, "対戦スタート",
                                       int(width * 0.5 - btn_w / 2), int(height * 0.85), btn_w, btn_h)

        return buttons

    # 結果ステップの描画
    def draw_result(self, screen, font, big_font, hp1, hp2, width, height,
                    player_images, action1, action2, battle_log,
                    frame, jump_progress1, jump_progress2, step, summary):

        winner = "P1" if hp1 > hp2 else "P2" if hp2 > hp1 else "引き分け"
        result_text = f"勝者: {winner}" if winner != "引き分け" else "引き分け！"
        draw_message_label(screen, result_text, width, height)

        # キャラクターとHPバーを常に表示
        draw_hp_bar(screen, font, int(width * 0.1), int(height * 0.05), hp1, "P1")
        draw_hp_bar(screen, font, int(width * 0.7), int(height * 0.05), hp2, "P2")

        if player_images.get("player1"):
            size1 = (400, 400) if winner == "P1" else (200, 200)  # 勝者なら2倍のサイズ
            x1 = int(width * 0.1)
            y1 = int(height * 0.5 - size1[1] // 2)  # Y軸を画面中央に調整
            img1 = pygame.transform.scale(player_images["player1"], size1)
            screen.blit(img1, (x1, y1))
            if winner == "P1":
                draw_sparkle_effect(screen, x1 + size1[0] // 2, y1 + size1[1] // 2, frame)  # キラキラエフェクト

        if player_images.get("player2"):
            size2 = (400, 400) if winner == "P2" else (200, 200)  # 勝者なら2倍のサイズ
            x2 = int(width * 0.7)
            y2 = int(height * 0.5 - size2[1] // 2)  # Y軸を画面中央に調整
            img2 = pygame.transform.scale(player_images["player2"], size2)
            screen.blit(img2, (x2, y2))
            if winner == "P2":
                draw_sparkle_effect(screen, x2 + size2[0] // 2, y2 + size2[1] // 2, frame)  # キラキラエフェクト

        # 総評を描画
        summary_x = int(width * 0.1)
        summary_y = int(height * 0.7)
        wrapped_lines = _wrap_text(summary, font, int(width * 0.8))
        for i, line in enumerate(wrapped_lines):
            surface = font.render(line, True, (0, 0, 0))
            screen.blit(surface, (summary_x, summary_y + i * font.get_linesize()))

        btn_w = int(width * 0.15)
        btn_h = int(height * 0.05)
        next_btn = draw_button(screen, font, "もう一度対戦",
                               int(width * 0.5 - btn_w / 2), int(height * 0.85),
                               btn_w, btn_h)
        buttons = {"next": next_btn}  # buttonsをローカル変数として定義
        return {"next": next_btn}

# 戦闘ステップの描画
def draw_battle(screen, font, big_font, log_font, width, height, turn, step, hp1, hp2,
                player_images, action1, action2, battle_log, frame, jump_progress1, jump_progress2,
                live_commentary, player1_status, player2_status, player_data):

    # 背景をクリアして残像を防ぐ
    screen.fill((240, 240, 240))

    if turn > 1:
        draw_step_label(screen, turn - 1, width, height)

    if step == 2:
        offset1x, offset1y = get_anim_offset(action1, frame)
        offset2x, offset2y = get_anim_offset(action2, frame)
    else:
        offset1x, offset1y = get_anim_offset("待機", frame)
        offset2x, offset2y = get_anim_offset("待機", frame)

    if step == 1:
        # 攻撃前の待機ステップ → action1, 2 = 何も描画しない or 「ターン準備中」表示にする
        if (turn - 1 ) == 0:
            result_text = "バトル・スタート！"
        else:
            result_text = f"対戦 {turn - 1} GO!"
        result_label = big_font.render(result_text, True, (0, 0, 0)) # エフェクト前の大きな「対戦GO」
        screen.blit(result_label, (width // 2 - result_label.get_width() // 2, height // 2 - result_label.get_height() // 2))

    if player_images.get("player1"):
        x1 = int(width * 0.1 + offset1x)
        y1 = int(height * 0.3 + offset1y)
        img1 = pygame.transform.scale(player_images["player1"], (200, 200))

        if step == 2:    # 攻撃ターンのみ
            frame_now = pygame.time.get_ticks()
            if action1 == "攻撃":
                pygame.mixer.music.stop()
                pygame.mixer.music.load('music/fight_attack.wav')
                pygame.mixer.music.set_volume(default_volume)  # 音量を設定
                pygame.mixer.music.play()
                draw_attack_effect(screen, img1, x1, y1, "R")
            elif action1 == "魔法":
                draw_magic_effect(screen, img1, x1, y1, frame, "R")
            elif action1 == "防御":
                draw_defense_effect(screen, img1, x1, y1, "R", frame_now)
            elif action1 == "回復":
                draw_heal_effect(screen, player_images["player1"], x1, y1, frame_now)
            elif action1 == "ジャンプ":
                draw_jump_effect(screen, img1, x1, y1, jump_progress1)
        else:
            screen.blit(img1, (x1, y1))  # 通常描画

    if player_images.get("player2"):
        x2 = int(width * 0.7 - offset2x)
        y2 = int(height * 0.3 + offset2y)
        img2 = pygame.transform.scale(player_images["player2"], (200, 200))

        if step == 2:
            frame_now = pygame.time.get_ticks()
            if action2 == "攻撃":
                draw_attack_effect(screen, img2, x2, y2, "L")
            elif action2 == "魔法":
                draw_magic_effect(screen, img2, x2, y2, frame, "L")
            elif action2 == "防御":
                draw_defense_effect(screen, img2, x2, y2, "L", frame_now)
            elif action2 == "回復":
                draw_heal_effect(screen, player_images["player2"], x2, y2, frame_now)
            elif action2 == "ジャンプ":
                draw_jump_effect(screen, img2, x2, y2, jump_progress2)
        else:
            screen.blit(img2, (x2, y2))  # 通常描画

    # 戦闘中、プレイヤーのステータスを描画
    if player_data.get("player1") and player_data.get("player2"):
        draw_status(
            screen,
            player_data["player1"],
            player_data["player2"],
            x1=10, y1=110, # プレイヤー1の描画位置を調整
            x2=width - 300, y2=110  # プレイヤー2の描画位置を調整
        )

    # HPバーと実況コメントを最後に描画
    draw_hp_bar(screen, font, int(width * 0.1), int(height * 0.05), hp1, "P1")
    draw_hp_bar(screen, font, int(width * 0.7), int(height * 0.05), hp2, "P2")

    # 実況コメントを描画
    commentary_x = int(width * 0.1)
    commentary_y = int(height * 0.6)
    max_commentary_width = int(width * 0.8)
    wrapped_lines = _wrap_text(live_commentary or "", log_font, max_commentary_width)
    line_h = log_font.get_linesize()
    for i, line in enumerate(wrapped_lines):
        surface = log_font.render(line, True, (0, 0, 0))
        screen.blit(surface, (commentary_x, commentary_y + i * line_h))

    # 対戦バトルのログを表示（画面中央）灰色
    log_y = int(height * 0.08) + log_font.get_height()
    for line in battle_log:  # ログを正順に表示
        log_surface = log_font.render(line, True, (200, 200, 200))
        log_rect = log_surface.get_rect(center=(width // 2, log_y))
        screen.blit(log_surface, log_rect)
        log_y += int(height * 0.025)


def _wrap_text(text: str, font, max_width: int):
    """
    フォントのピクセル幅に合わせて改行位置を決める（CJK対応: 文字単位）。
    """
    lines = []
    if not text:
        return lines
    for paragraph in str(text).split("\n"):
        if paragraph == "":
            lines.append("")
            continue
        buf = ""
        for ch in paragraph:
            test = buf + ch
            if font.size(test)[0] <= max_width:
                buf = test
            else:
                lines.append(buf)
                buf = ch
        lines.append(buf)
    return lines

