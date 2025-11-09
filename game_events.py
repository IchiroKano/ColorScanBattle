import pygame

# イベント管理クラス
class EventManager:
    def __init__(self, player_manager):
        self.player_manager = player_manager

    # ステージ画面と結果画面のイベント処理
    def handle_events(self, stage, buttons, player_data, player_images, eyecatch_images, now, events):
        for event in events:  # イベントリストをループ処理
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: # どの画面でもESCキーで終了
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if stage == "staging": # ステージング画面のボタン処理
                    if buttons.get("reload1") and buttons["reload1"].collidepoint(mx, my):
                        self.player_manager.load_player("player1")
                        return "reload1"
                    elif buttons.get("reload2") and buttons["reload2"].collidepoint(mx, my):
                        self.player_manager.load_player("player2")
                        return "reload2"
                    elif buttons.get("start") and buttons["start"].collidepoint(mx, my):
                        return "start"
                    elif buttons.get("quit") and buttons["quit"].collidepoint(mx, my):
                        return "quit"
                elif stage == "result": # 結果画面のボタン処理
                    if buttons.get("next"):
                        if buttons["next"].collidepoint(mx, my):
                            return "next"
        return None