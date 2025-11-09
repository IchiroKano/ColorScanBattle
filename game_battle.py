import random
from game_utils import log_to_file

ACTIONS = ["攻撃", "防御", "回復", "魔法", "ジャンプ"]

# ランダムに行動を選択する（攻撃, 防御, 回復, 魔法, ジャンプ）
def choose_action(player_data):
    return random.choice(ACTIONS)

# 行動を適用してダメージ計算を行う
def apply_action(p1, p2, action1, action2):
    log = [] # 戦闘ログ
    # ステータスを辞書から取り出す（初期化済みの player_data を使う）
    hp1, hp2 = p1["体力"], p2["体力"]
    atk1, atk2 = p1["攻撃力"], p2["攻撃力"]
    def1, def2 = p1["防御力"], p2["防御力"]
    spd1, spd2 = p1["すばやさ"], p2["すばやさ"]
    heal1, heal2 = p1["回復力"], p2["回復力"]
    ev1, ev2 = float(p1["回避力"]), float(p2["回避力"])

    # プレイヤー１のアクション：パラメータ更新
    dmg_to_2 = resolve_action(action1, action2, atk1, spd1, def2, ev2) # プレイヤー2へのダメージ計算
    hp2 = max(0, int(hp2 - dmg_to_2))                                  # プレイヤー2の体力更新
    if action1 == "回復":
        heal_amount = int(heal1 / 2)  # 回復力の半分を適用
        hp1 = min(100, hp1 + heal_amount)  # HPは最大100まで
    log.append(f"P1の行動: {action1} → P2に{dmg_to_2}ダメージ")         # ログ記録

    # プレイヤー２のアクション：パラメータ更新
    dmg_to_1 = resolve_action(action2, action1, atk2, spd2, def1, ev1)
    hp1 = max(0, int(hp1 - dmg_to_1))
    if action2 == "回復":
        heal_amount = int(heal2 / 2) 
        hp2 = min(100, hp2 + heal_amount)
    log.append(f"P2の行動: {action2} → P1に{dmg_to_1}ダメージ")

    # 更新された体力を辞書に戻す
    p1["体力"], p2["体力"] = hp1, hp2
    return hp1, hp2, log

# 行動の組み合わせに基づいてダメージを計算する
def resolve_action(my_action, opp_action, atk, spd, def_, opp_ev):
    if random.random() < opp_ev / 100:  # 回避判定（回避力をそのまま%として使用）
        log_to_file(f"info: {my_action} に対して、相手が回避しました。")
        return 0  # 攻撃を無効化

    if my_action == "攻撃":
        damage = atk - def_  # 攻撃力 - 防御力
        if opp_action == "ジャンプ":
            damage //= 2  # ジャンプ中はダメージ半減
        damage = max(1, damage)  # 最小ダメージは1
        log_to_file(f"計算: 攻撃ダメージ = {damage} (攻撃力: {atk}, 防御力: {def_}, ジャンプ補正: {opp_action == 'ジャンプ'})")
        if damage == 1 and random.random() < spd / 100:  # すばやさ%の確率で追加ダメージ
            bonus_damage = random.randint(2, 5)
            damage += bonus_damage
            log_to_file(f"計算: 最小ダメージ補正 = {bonus_damage} 加算され、最終ダメージ: {damage}")
        return damage

    elif my_action == "魔法":
        damage = spd - def_ // 2  # すばやさ - 防御力の半分
        damage = max(1, damage)  # 最小ダメージは1
        log_to_file(f"計算: 魔法ダメージ = {damage} (すばやさ: {spd}, 防御力: {def_})")
        if damage == 1 and random.random() < spd / 100:  # すばやさ%の確率で追加ダメージ
            bonus_damage = random.randint(2, 5)
            damage += bonus_damage
            log_to_file(f"計算: 最小ダメージ補正 = {bonus_damage} 加算され、最終ダメージ: {damage}")
        return damage

    elif my_action == "ジャンプ":
        damage = atk * 0.5 - def_ / 3  # 攻撃力の50% - 防御力の1/3
        damage = max(1, int(damage))  # 最小ダメージは1
        log_to_file(f"計算: ジャンプダメージ = {damage} (攻撃力: {atk}, 防御力: {def_})")
        if damage == 1 and random.random() < spd / 100:  # すばやさ%の確率で追加ダメージ
            bonus_damage = random.randint(2, 5)
            damage += bonus_damage
            log_to_file(f"info: 最小ダメージ補正: {bonus_damage} 加算され、最終ダメージ: {damage}")
        return damage

    elif my_action == "回復":
        log_to_file("info: 回復行動のためダメージなし。")
        return 0  # 回復はダメージを与えない

    log_to_file("info: その他の行動のためダメージなし。")
    return 0  # その他の行動はダメージなし

# プレイヤーの初期HPを計算する関数を追加
def calculate_initial_hp(base_hp):
    """
    プレイヤーの初期HPを計算する関数。
    :param base_hp: 基本HPの値
    :return: 計算されたHP（50以上100以下に制限）
    """
    return max(50, min(100, base_hp))  # 50以上100以下に制限

def calculate_initial_param(param_name, base_value):
    """
    プレイヤーの初期パラメータを計算する関数。
    :param param_name: パラメータ名（例: "攻撃力", "回避力"）
    :param base_value: 基本パラメータの値
    :return: 計算されたパラメータ（50以上100以下に制限）
    """
    if param_name == "回避力":
        return max(50, min(100, base_value))  # 回避力はそのまま
    return max(50, min(100, 50 + base_value))  # 他のパラメータは50を加算

class BattleManager:
    def __init__(self, player_data):
        self.player_data = player_data
        self.original_player_data = {  # 初期値を保持
            "player1": player_data["player1"].copy(),
            "player2": player_data["player2"].copy()
        }
        self.turn = 1
        self.step = 1
        self.hp1 = calculate_initial_hp(player_data["player1"]["体力"])
        self.hp2 = calculate_initial_hp(player_data["player2"]["体力"])
        self.player_data["player1"]["体力"] = self.hp1  # 初期HPをplayer_dataに反映
        self.player_data["player2"]["体力"] = self.hp2  # 初期HPをplayer_dataに反映
        self.battle_log = []
        self.action1 = ""
        self.action2 = ""
        self.timer = 0
        self.jump_start_frame1 = 0
        self.jump_start_frame2 = 0

    def advance_step(self, now):

        if self.turn > 7:
            return "result"

        if self.step == 1 and now - self.timer >= 2000:  # ステップ1の遅延を2秒に設定
            self.battle_log.append(f"対戦 {self.turn} GO!")
            log_to_file(f"\n//----- 対戦 {self.turn} GO!")
            self.step = 2
            self.timer = now

        elif self.step == 2 and now - self.timer >= 3000:
            self.action1 = choose_action(self.player_data["player1"]) # プレイヤー1の行動選択
            self.action2 = choose_action(self.player_data["player2"]) # プレイヤー2の行動選択
            # ↓ 行動適用とダメージ計算
            self.hp1, self.hp2, log = apply_action(self.player_data["player1"], self.player_data["player2"], self.action1, self.action2)
            self.battle_log.append(f"ターン{self.turn}")
            log_to_file(f"ターン{self.turn}")
            self.battle_log.extend(log)
            for log_entry in log:
                log_to_file(log_entry)
            log_to_file(f"P1 HP: {self.hp1}, P2 HP: {self.hp2}")
            self.step = 3
            self.timer = now

        elif self.step == 3 and now - self.timer >= 1000:
            self.turn += 1
            self.step = 1
            self.timer = now
            log_to_file(f"info: ターン{self.turn}に進行しました。")

        return "battle"

    def is_battle_over(self):
        return self.turn > 7 or self.hp1 <= 0 or self.hp2 <= 0