import pygame
import os
import json
from game_utils import convert_param, log_to_file
from game_ai import add_player_parameters

# プレイヤーのオブジェクト
class PlayerManager:
    # 初期化
    def __init__(self):
        self.player_data = {}
        self.player_images = {}
        self.eyecatch_images = {}

    # JSONデータと画像の読み込み
    def load_player(self, player_key):
        try:
            # キャッシュを利用して画像を再利用
            if player_key in self.player_images:
                return

            # JSONファイルの読み込み
            spec_file = "player_spec1.json" if player_key == "player1" else "player_spec2.json"
            with open(spec_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # ステータスを50〜100の範囲に変換
            for key in ["攻撃力", "防御力", "すばやさ", "回復力", "体力", "回避力"]:
                if key == "回避力":
                    data[key] = data[key]  # convert_param を使用しない
                else:
                    data[key] = convert_param(data[key])

            self.player_data[player_key] = data

            # パラメータ計算後のログ出力
            log_to_file(f"ステージング(ロード完了)： {player_key} : 攻撃力={data['攻撃力']}, 防御力={data['防御力']}, すばやさ={data['すばやさ']}, 回復力={data['回復力']}, 回避力={data['回避力']}, 体力={data['体力']}, 色系統={data['色系統']}, キャラ名={data['キャラ名']}, スキルセット={data['スキルセット']}, 画像ファイル={data['画像ファイル']}")
            add_player_parameters(f"{player_key} : 色系統={data['色系統']}, キャラ名={data['キャラ名']}, スキルセット={data['スキルセット']}")

            # キャラクター画像の読み込み
            img_path = os.path.join("img", data["画像ファイル"])
            original_image = pygame.image.load(img_path)
            if player_key == "player1":
                self.player_images[player_key] = pygame.transform.flip(original_image, True, False)
            else:
                self.player_images[player_key] = original_image

            # アイキャッチ画像の読み込み
            eyecatch_path = os.path.join("img", f"char-{data['色系統']}.png")
            self.eyecatch_images[player_key] = pygame.image.load(eyecatch_path)

        except Exception as e:
            print(f"{player_key} 読み込み失敗:", e)

# プレイヤー情報を、ステージング画面に描画
def draw_player_info(screen, font, bold_font, data, image, x, width, height):
    y = int(height * 0.15)
    line_h = int(height * 0.045)
    bar_max_width = int(width * 0.2)
    bar_height = int(line_h * 0.6)

    screen.blit(bold_font.render(data["キャラ名"], True, (0, 0, 0)), (x, y))
    y += line_h

    for label, key in [("攻撃力", "攻撃力"), ("防御力", "防御力"), ("すばやさ", "すばやさ"),
                       ("回復力", "回復力"), ("体力", "体力")]:
        bar_x = x
        bar_y = y + int((line_h - bar_height) / 2)
        bar_width = int(bar_max_width * data[key] / 100)

        pygame.draw.rect(screen, (100, 200, 100), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_max_width, bar_height), 2)

        value_surface = font.render(str(data[key]), True, (0, 0, 0))
        label_surface = font.render(label, True, (0, 0, 0))
        screen.blit(value_surface, (bar_x + bar_max_width + 10, y))
        screen.blit(label_surface, (bar_x + bar_max_width + 80, y))

        y += line_h

    evasion = float(data["回避力"])
    screen.blit(font.render(f"回避率: {int(evasion)}%", True, (0, 0, 0)), (x, y))
    y += line_h

    skill_rect = pygame.Rect(x, y, int(width * 0.25), line_h * 3 + 20)
    pygame.draw.rect(screen, (0, 0, 0), skill_rect, 2)

    skill_y = y + 10
    screen.blit(font.render(f"スキル1: {data['スキルセット']['skill1']}", True, (0, 80, 0)), (x + 10, skill_y)); skill_y += line_h
    screen.blit(font.render(f"スキル2: {data['スキルセット']['skill2']}", True, (0, 80, 0)), (x + 10, skill_y)); skill_y += line_h
    screen.blit(font.render(f"スキル3: {data['スキルセット']['skill3']}", True, (0, 80, 0)), (x + 10, skill_y))

    if image:
        img_w, img_h = image.get_size()
        scale = 0.5
        image = pygame.transform.scale(image, (int(img_w * scale), int(img_h * scale)))
        screen.blit(image, (x, int(height * 0.6)))

