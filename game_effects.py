import pygame
import math
import random
from game_utils import music_files, load_sounds, default_volume

# pygame.mixerの初期化
pygame.mixer.init()

# 効果音をロード
sounds = load_sounds()

# 効果音の再生前に音量を設定
sounds['attack'].set_volume(default_volume)
sounds['magic'].set_volume(default_volume)
sounds['defence'].set_volume(default_volume)
sounds['jump'].set_volume(default_volume)
sounds['healing'].set_volume(default_volume)

# 攻撃エフェクト
def draw_attack_effect(screen, img, x, y, side):
    sounds['attack'].play()  # 攻撃音を再生

    screen.blit(img, (x, y))  # 待機
    if side == "L":
        points = [(x + 200, y + 100), (x + 250, y + 80), (x + 250, y + 120)]
    elif side == "R":
        points = [(x, y + 100), (x - 50, y + 80), (x - 50, y + 120)]
    else:
        return
    pygame.draw.polygon(screen, (255, 0, 0), points)

# 魔法エフェクト
def draw_magic_effect(screen, img, x, y, frame, side):
    sounds['magic'].play()  # 魔法音を再生

    screen.blit(img, (x, y))  # 待機
    size = min((frame % 60) * 3, 180)
    angle = (frame * 3) % 360
    line_width = 4
    r = min(255, 100 + frame % 100)
    g = 100
    b = max(100, 255 - frame % 100)
    color = (r, g, b)

    dx = -(frame % 60) * 3 if side == "L" else (frame % 60) * 3 if side == "R" else 0
    center = (x + 100 + dx, y + 100)

    layer = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    cx, cy = size, size

    tri1 = [(cx, cy - size), (cx - size * 0.866, cy + size / 2), (cx + size * 0.866, cy + size / 2)]
    tri2 = [(cx, cy + size), (cx - size * 0.866, cy - size / 2), (cx + size * 0.866, cy - size / 2)]

    pygame.draw.polygon(layer, color, tri1, width=line_width)
    pygame.draw.polygon(layer, color, tri2, width=line_width)
    pygame.draw.circle(layer, color, (cx, cy), size // 3, width=line_width)

    rotated = pygame.transform.rotate(layer, angle)
    rect = rotated.get_rect(center=center)
    screen.blit(rotated, rect.topleft)

# 攻撃・魔法のアタックアニメーション
def get_anim_offset(action, frame):
    # アニメーション周期（長くするほどゆっくり）
    duration = 30  # 60フレーム = 約1秒
    phase = frame % duration
    progress = phase / duration  # 0.0〜1.0 の進行度
    max_offset = 100  # 最大移動距離（px）

    if action == "攻撃":
        # 前半で進み、後半で戻る（イーズイン・アウト風）
        if progress < 0.5:
            return int(max_offset * (progress * 2)), 0  # 0〜100
        else:
            return int(max_offset * (1 - (progress - 0.5) * 2)), 0  # 100〜0
    elif action == "魔法":
        # 魔法は攻撃と同じ左右に動きアタック
        return int(-max_offset * abs(progress - 0.5) * 2), 0  # -100〜0〜-100
    elif action == "ジャンプ":
        # 縦方向にぴよーん
        return 0, int(-max_offset * math.sin(math.pi * progress))
    return 0, 0 # リターンはx,y

# 防御エフェクト
def draw_defense_effect(screen, img, x, y, direction, frame=0):
    sounds['defence'].play()  # 防御音を再生
    screen.blit(img, (x, y))  # 待機
    color = (100, 100, 255)
    # シールドのX位置
    shield_x = x + 180 if direction == "R" else x - 20
    # フレームに応じて上下に揺れるYオフセット（sin波）
    offset = int(20 * math.sin(frame * 0.1))  # 振幅20px、周期調整
    # シールド描画（上下に動く）
    pygame.draw.rect(screen, color, (shield_x, y + offset, 10, 200))

# ジャンプエフェクト
def draw_jump_effect(screen, image, x, y, progress, duration=480, jump_height=150):
    sounds['jump'].play()  # ジャンプ音を再生
    # ジャンプ中のYオフセットを計算（sin波で滑らかに）
    radians = math.pi * progress / duration
    y_offset = -jump_height * math.sin(radians)  # 頂点で最大ジャンプ
    screen.blit(image, (x, y + y_offset))

# 回復エフェクト -------------------------------------------------------
# 泡の構造体
class Bubble:
    def __init__(self, x, y):
        self.x = x + random.randint(-70, 70)
        self.y = y + 200
        self.radius = random.randint(5, 15)
        self.speed = random.uniform(0.5, 2.0)
        self.alpha = 255

    def update(self):
        self.y -= self.speed
        self.alpha -= 2  # 徐々に消える

    def is_alive(self):
        return self.alpha > 0

    def draw(self, surface):
        bubble_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        bubble_surface.set_alpha(self.alpha)  # 透明度をここで設定
        pygame.draw.circle(bubble_surface, (100, 255, 100), (self.radius, self.radius), self.radius)
        surface.blit(bubble_surface, (self.x - self.radius, self.y - self.radius))

# グローバル泡リスト（呼び出し元で管理）
bubbles = []

def draw_heal_effect(screen, img, x, y, frame):
    sounds['healing'].play()  # 回復音を再生

    screen.blit(img, (x, y))  # 待機
    # 毎フレーム数個の泡を追加
    if frame % 5 == 0:
        for _ in range(3):
            bubbles.append(Bubble(x + 100, y - 30))
    # 泡を更新・描画
    for bubble in bubbles[:]:
        bubble.update()
        bubble.draw(screen)
        if not bubble.is_alive():
            bubbles.remove(bubble)

def draw_sparkle_effect(screen, x, y, frame):
    """
    キラキラのエフェクトを描画する関数。
    :param screen: Pygameの画面オブジェクト
    :param x: エフェクトの中心X座標
    :param y: エフェクトの中心Y座標
    :param frame: 現在のフレーム数
    """
    for i in range(8):  # 複数のキラキラを描画
        angle = (i * 45)  # 45度間隔で配置
        radius = (frame % 60) * 4  # 半径が広がるアニメーション
        size = 5 + (frame % 20)  # サイズを変化させる
        color = (255, 255, 100, max(0, 255 - radius * 1))  # 黄色っぽい色で透明度を調整
        dx = int(math.cos(math.radians(angle)) * radius)
        dy = int(math.sin(math.radians(angle)) * radius)

        sparkle_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(sparkle_surface, color, (size // 2, size // 2), size // 2)
        screen.blit(sparkle_surface, (x + dx - size // 2, y + dy - size // 2))
