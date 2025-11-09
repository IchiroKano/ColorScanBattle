#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cv2
import numpy as np
import json
import win32com.client
import sys
from convert_to_player import convert_color_to_player
from PIL import Image, ImageDraw, ImageFont
import pygame

# pygameの初期化
pygame.init()
pygame.mixer.init()

# 音楽ファイルのロード
music_files = {
    'q': "music/stage_base.wav",
    'w': "music/stage_left.wav",
    'e': "music/stage_right.wav"
}

# 起動オプションでカメラを切り替え
try:
    cam_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
except ValueError:
    print("カメラインデックスは整数で指定してください。例: python video_lefo_full.py 1")
    sys.exit(1)

saved_color_areas = {}  # 初期値
print("[ESC]終了 [Q]規準色を記憶 [W]プレイヤー１出力 [E]プレイヤー２出力")
print(f"使用するカメラは: {cam_index}")

# カメラを選ぶ [0]内蔵カメラ [1]USB外付けカメラ
camera = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
# camera = cv2.VideoCapture(0)
print("Camera opened:", camera.isOpened())
print("Frame size:", camera.get(cv2.CAP_PROP_FRAME_WIDTH), "x", camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

# デバッグ

# WMIでカメラ名一覧を取得
def get_camera_names():
    names = []
    wmi = win32com.client.GetObject("winmgmts:")
    for cam in wmi.InstancesOf("Win32_PnPEntity"):
        if cam.Name and ("Camera" in cam.Name or "Video" in cam.Name):
            names.append(cam.Name)
    return names

# OpenCVで使用可能なカメラを確認
def list_available_cameras():
    camera_names = get_camera_names()
    found = 0
    for i in range(2):              #検索するカメラを２台にする
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            name = camera_names[found] if found < len(camera_names) else "Unknown"
            print(f"Camera {i} is available → {name}")
            found += 1
        else:
            print(f"Camera {i} is not available")
        cap.release()

list_available_cameras()

camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
#camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('Y','U','Y','V')) デスクトップPC
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
camera.set(cv2.CAP_PROP_FPS, 3)

# 色定義辞書
color_ranges = {
    "Red1":     [(0, 100, 100), (10, 255, 255), (0, 0, 255)],
    "Red2":     [(160, 100, 100), (180, 255, 255), (0, 0, 255)],
    "Orange":   [(11, 100, 100), (25, 255, 255), (0, 165, 255)],
    "Yellow":   [(26, 100, 100), (35, 255, 255), (0, 255, 255)],
    "Green":    [(40, 70, 70),   (80, 255, 255), (0, 255, 0)],
    "LightGreen":[(36, 50, 50), (55, 255, 255), (144, 238, 144)],
    "Cyan":     [(81, 100, 100), (95, 255, 255), (255, 255, 0)],
    "Blue":     [(96, 100, 100), (130, 255, 255), (255, 0, 0)],
    "Pink":     [(131, 100, 100), (160, 255, 255), (255, 192, 203)],
    "Purple":   [(141, 100, 100), (169, 255, 255), (128, 0, 128)],
    "Gray":     [(0, 0, 60),    (180, 30, 220),  (128,128,128)],
    "White":    [(0, 0, 200),    (180, 30, 255), (255, 255, 255)]
}

def detect_color(hsv, img, name, lower, upper, draw_color):
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 300:
            total_area += area
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(img, (x, y), (x+w, y+h), draw_color, 2)
            cv2.putText(img, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)
    return total_area

def save_diff_and_generate_player(color_areas, saved_color_areas, output_filename):
    if not saved_color_areas:
        print("記憶された色面積がありません（Qキーで記憶してください）")
        return

    total_area = sum(color_areas.values())
    diff_map = {}
    for name in color_ranges.keys():
        current_area = color_areas.get(name, 0)
        saved_area = saved_color_areas.get(name, 0)
        if current_area != saved_area:
            ratio = round((current_area / total_area) * 100, 1) if total_area > 0 else 0.0
            diff_map[name] = ratio
        else:
            diff_map[name] = 0.0

    with open("color_map.json", "w", encoding="utf-8") as f:
        json.dump(diff_map, f, ensure_ascii=False, indent=2)
    print("差分（割合%）を color_map.json に保存しました")

    player = convert_color_to_player("color_map.json", output_filename)
    print(f"{output_filename} を出力しました:", player)

# メッセージをcv2画面に表示する関数
def display_message(img, message, width, height):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    color = (255, 255, 255)  # 白色
    thickness = 3
    bg_color = (255, 0, 0)  # 青色
    text_size = cv2.getTextSize(message, font, font_scale, thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    # 背景の四角形を描画
    cv2.rectangle(img, (text_x - 10, text_y - text_size[1] - 10),
                  (text_x + text_size[0] + 10, text_y + 10), bg_color, -1)
    # テキストを描画
    cv2.putText(img, message, (text_x, text_y), font, font_scale, color, thickness)

# 日本語テキストを描画する関数（背景付き）
def draw_japanese_text_with_background(img, text, position, font_path="C:/Windows/Fonts/meiryo.ttc", font_size=32, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    # OpenCVの画像をPillow形式に変換
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    # フォントを指定
    font = ImageFont.truetype(font_path, font_size)
    # テキストサイズを取得
    text_bbox = draw.textbbox((0, 0), text, font=font)  # テキストのバウンディングボックスを取得
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x, text_y = position
    # 背景の四角形を描画
    draw.rectangle([text_x, text_y, text_x + text_width + 10, text_y + text_height + 10], fill=bg_color)
    # テキストを描画
    draw.text((text_x + 5, text_y + 5), text, font=font, fill=text_color)
    # Pillow画像をOpenCV形式に戻す
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

while True:
    ret, frame = camera.read()
    if not ret:
        break
    imgFlip = frame
    if imgFlip is not None and imgFlip.shape[-1] == 3:
        hsv = cv2.cvtColor(imgFlip, cv2.COLOR_BGR2HSV)
    else:
        print("画像が取得できないか、カラー画像ではありません")
        continue  # または break、pass など適切に処理

    color_areas = {}
    for name, (lower, upper, bgr) in color_ranges.items():
        area = detect_color(hsv, imgFlip, name, lower, upper, bgr)
        color_areas[name] = int(area)

    # 横棒グラフ描画
    x_start = 150
    y_offset = 20
    bar_max_width = 300
    max_area = max(color_areas.values()) if color_areas else 0

    if max_area > 0:
        for name, area in color_areas.items():
            bgr = color_ranges[name][2]
            bar_width = int((area / max_area) * bar_max_width)
            cv2.putText(imgFlip, name, (10, y_offset + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bgr, 1)
            cv2.rectangle(imgFlip, (x_start, y_offset), (x_start + bar_width, y_offset + 15), bgr, -1)
            cv2.putText(imgFlip, str(area), (x_start + bar_width + 5, y_offset + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, bgr, 1)
            y_offset += 25
    else:
        cv2.putText(imgFlip, "No color detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow("Frame", imgFlip)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break
    elif key == ord('q'):
        saved_color_areas = color_areas.copy()
        print("色面積を記憶しました")
        pygame.mixer.music.load(music_files['q'])
        pygame.mixer.music.play()
        imgFlip = draw_japanese_text_with_background(imgFlip, "基準をリセットしました", (200, 300))
        cv2.imshow("Frame", imgFlip)
        cv2.waitKey(3000)  # 3秒間待機
    elif key == ord('w'):
        save_diff_and_generate_player(color_areas, saved_color_areas, "player_spec1.json")
        pygame.mixer.music.load(music_files['w'])
        pygame.mixer.music.play()
        imgFlip = draw_japanese_text_with_background(imgFlip, "プレイヤー１を認識しました", (200, 300))
        cv2.imshow("Frame", imgFlip)
        cv2.waitKey(3000)  # 3秒間待機
    elif key == ord('e'):
        save_diff_and_generate_player(color_areas, saved_color_areas, "player_spec2.json")
        pygame.mixer.music.load(music_files['e'])
        pygame.mixer.music.play()
        imgFlip = draw_japanese_text_with_background(imgFlip, "プレイヤー２を認識しました", (200, 300))
        cv2.imshow("Frame", imgFlip)
        cv2.waitKey(3000)  # 3秒間待機

print("終了します")
camera.release()
cv2.destroyAllWindows()
