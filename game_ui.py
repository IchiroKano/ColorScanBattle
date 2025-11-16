import pygame

# フォント取得関数にフォールバック処理を追加
def get_fonts(height):
    try:
        font = pygame.font.SysFont("Meiryo", int(height * 0.035))
        bold_font = pygame.font.SysFont("Meiryo", int(height * 0.04), bold=True)
        log_font = pygame.font.SysFont("Meiryo", int(height * 0.02))
        big_font = pygame.font.SysFont("Meiryo", int(height * 0.07))
    except Exception as e:
        print("[WARNING] Meiryoフォントのロードに失敗しました。デフォルトフォントを使用します。")
        font = pygame.font.Font(None, int(height * 0.035))
        bold_font = pygame.font.Font(None, int(height * 0.04))
        log_font = pygame.font.Font(None, int(height * 0.02))
        big_font = pygame.font.Font(None, int(height * 0.07))
    return font, bold_font, log_font, big_font

# ボタン描画（青色背景: 30,120,200, 文字色：白）
def draw_button(screen, font, text, x, y, w, h):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, (30, 120, 200), rect)
    label = font.render(text, True, (255, 255, 255))
    label_rect = label.get_rect(center=(x + w // 2, y + h // 2))
    screen.blit(label, label_rect)
    return rect

# HPバー描画
def draw_hp_bar(screen, font, x, y, hp, label):
    bar_w = int(screen.get_width() * 0.2)
    bar_h = int(screen.get_height() * 0.03)
    pygame.draw.rect(screen, (0, 0, 0), (x, y, bar_w, bar_h), 2)
    fill_w = int(bar_w * hp / 100)
    color = (255 - hp * 2, hp * 2, 50)
    pygame.draw.rect(screen, color, (x, y, fill_w, bar_h))
    # HPのラベル表示を削除
    screen.blit(font.render(f"{label}: {hp}", True, (0, 0, 0)), (x, y - 50))

# 「ターン１」「ターン２」を表示するラベル描画（青色BOX, 白色テキスト）
def draw_step_label(screen, turn, width, height):
    box_w = int(width * 0.2)
    box_h = int(height * 0.06)
    box_x = int((width - box_w) / 2)
    box_y = int(height * 0.02)
    pygame.draw.rect(screen, (30, 120, 200), (box_x, box_y, box_w, box_h))
    font = pygame.font.SysFont("Meiryo", int(height * 0.03), bold=True)
    label = font.render(f"ターン {turn}", True, (255, 255, 255))
    label_rect = label.get_rect(center=(box_x + box_w // 2, box_y + box_h // 2))
    screen.blit(label, label_rect)

# 「Loading...」などを表示するラベル描画（青色BOX, 白色テキスト）
def draw_message_label(screen, message, width, height):
    box_w = int(width * 0.2)
    box_h = int(height * 0.06)
    box_x = int((width - box_w) / 2)
    box_y = int((height - box_h) / 2)
    pygame.draw.rect(screen, (30, 120, 200), (box_x, box_y, box_w, box_h))
    font = pygame.font.SysFont("Meiryo", int(height * 0.03), bold=True)
    label = font.render(f"{message}", True, (255, 255, 255)) # 白色 255,255,255
    label_rect = label.get_rect(center=(box_x + box_w // 2, box_y + box_h // 2))
    screen.blit(label, label_rect)

# プレイヤーのステータス表示
def draw_status(screen, player1_status, player2_status, x1=10, y1=None, x2=None, y2=None):
    """
    プレイヤーのステータスを画面端に表示する関数。
    ステータス名は漢字2文字に制限し、HPグラフの下に表示。
    :param screen: Pygameの画面オブジェクト
    :param player1_status: プレイヤー1のステータス辞書
    :param player2_status: プレイヤー2のステータス辞書
    :param x1, y1: プレイヤー1の描画開始位置
    :param x2, y2: プレイヤー2の描画開始位置
    """
    font = pygame.font.SysFont("Meiryo", 24)  # 日本語対応フォントを指定

    # デフォルトの描画位置を設定
    if y1 is None:
        y1 = screen.get_height()/2
    if x2 is None:
        x2 = screen.get_width() - 200
    if y2 is None:
        y2 = screen.get_height()/2

    # 表示するキーをフィルタリング（スキルや画像ファイル名を除外）
    keys_to_display = [key for key in player1_status.keys() if key not in ["スキルセット", "画像ファイル"]][:8]

    # プレイヤー1のステータスを描画
    for key in keys_to_display:
        value = player1_status.get(key, "-")
        label = key[:2]  # 表示用ラベルを漢字2文字に制限
        text_surface = font.render(f"{label}: {value}", True, (0, 0, 0))  # 黒色で描画
        screen.blit(text_surface, (x1, y1))
        y1 += 23  # 次の行に移動

    # プレイヤー2のステータスを描画
    for key in keys_to_display:
        value = player2_status.get(key, "-")
        label = key[:2]  # 表示用ラベルを漢字2文字に制限
        text_surface = font.render(f"{label}: {value}", True, (0, 0, 0))  # 黒色で描画
        text_width = text_surface.get_width()
        x2_adjusted = x2 - text_width  # テキスト幅に応じて左にずらす
        screen.blit(text_surface, (x2_adjusted, y2))
        y2 += 23  # 次の行に移動

def draw_ai_status(screen, message, width, height):
    """
    AIの利用可否を画面に表示する関数。"Loading"表示のみ。ならば後で削除するか。
    """
    font = pygame.font.Font(None, 36)
    text = font.render(message, True, (255, 255, 255))
    text_rect = text.get_rect(center=(width // 2, height // 10))
    pygame.draw.rect(screen, (0, 0, 0), text_rect.inflate(20, 10))
    screen.blit(text, text_rect)