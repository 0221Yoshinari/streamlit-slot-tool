import streamlit as st
from scipy.stats import poisson

# --- 定義データ ---
# 各設定ごとのスペック・確率情報
# 数値は全て1/X.Xの場合のX.X、または%の場合の小数（例: 0.27%は0.0027）
GAME_DATA = {
    "AT初当り確率": {1: 394.4, 2: 380.5, 3: 357.0, 4: 325.9, 5: 291.2, 6: 261.3},
    "CZ出現率トータル": {1: 262.6, 2: 255.6, 3: 246.5, 4: 233.1, 5: 216.4, 6: 203.7},
    "CZ_レミニセンス当選率": {1: 300.5, 2: 295.1, 3: 287.6, 4: 276.7, 5: 262.7, 6: 251.2},
    "CZ_大喰らいのリゼ当選率": {1: 2079.1, 2: 1906.5, 3: 1722.8, 4: 1478.9, 5: 1226.6, 6: 1074.9},
    "弱チェリーCZ当選率_通常滞在時": {1: 0.0027, 2: 0.0029, 3: 0.0031, 4: 0.0033, 5: 0.0038, 6: 0.0043},
    "弱チェリーCZ当選率_高確滞在時": {1: 0.0059, 2: 0.0063, 3: 0.0069, 4: 0.0073, 5: 0.0083, 6: 0.0095},
    "規定ゲーム数150G以内CZ当選率": {1: 0.1958, 2: 0.2104, 3: 0.2315, 4: 0.2637, 5: 0.3196, 6: 0.3601},
    "下段リプレイ出現率": {1: 1260.3, 2: 1213.6, 3: 1170.3, 4: 1129.9, 5: 1092.3, 6: 1024.0},
    "初当りエピソードボーナス当選率": {1: 6620.2, 2: 5879.7, 3: 5114.5, 4: 4062.5, 5: 3166.7, 6: 2639.5},
    "精神世界ステージ滞在G数_10G": {1: 0.64, 2: 0.60, 3: 0.56, 4: 0.52, 5: 0.48, 6: 0.44},
    "精神世界ステージ滞在G数_20G": {1: 0.30, 2: 0.32, 3: 0.34, 4: 0.36, 5: 0.38, 6: 0.32},
    "精神世界ステージ滞在G数_30G": {1: 0.06, 2: 0.08, 3: 0.10, 4: 0.12, 5: 0.14, 6: 0.24},
    "引き戻し（即前兆）確率": {1: 0.0500, 2: 0.06, 3: 0.08, 4: 0.1000, 5: 0.1300, 6: 0.16},
    "通常時モード比率_通常A": {1: 0.28, 2: 0.26, 3: 0.23, 4: 0.20, 5: 0.17, 6: 0.14},
    "通常時モード比率_通常B": {1: 0.24, 2: 0.23, 3: 0.21, 4: 0.19, 5: 0.17, 6: 0.14},
    "通常時モード比率_通常C": {1: 0.14, 2: 0.15, 3: 0.16, 4: 0.17, 5: 0.18, 6: 0.14},
    "通常時モード比率_チャンス": {1: 0.14, 2: 0.14, 3: 0.14, 4: 0.14, 5: 0.14, 6: 0.14},
    "通常時モード比率_天国準備": {1: 0.06, 2: 0.06, 3: 0.08, 4: 0.09, 5: 0.10, 6: 0.18},
    "通常時モード比率_天国": {1: 0.14, 2: 0.16, 3: 0.18, 4: 0.21, 5: 0.24, 6: 0.28},
    "裏AT当選率_初当り経由": {1: 0.0110, 2: 0.0132, 3: 0.0163, 4: 0.0219, 5: 0.0285, 6: 0.0332},
}

# 示唆系のデータ（回数を入力するため、示唆ごとの確率変動率を設定）
# type: exact, min_setting, exclude_setting, even_settings, odd_settings, normal
# value_multiplier: 示唆が出た場合に、その設定の尤度をどれだけ強く（または弱く）するか
HINT_DATA = {
    "CZ失敗時カード_鈴屋什造（赤枠）": {"type": "even_settings", "settings": [2, 4, 6], "value_multiplier": 5.0}, # 偶数設定濃厚
    "CZ失敗時カード_泉（金枠）": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0}, # 設定4以上濃厚
    "CZ失敗時カード_有馬貴将（虹枠）": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0}, # 設定6濃厚

    "滞納状況示唆_僕にはディナーでもどうだい？": {"type": "even_settings", "settings": [2, 4, 6], "value_multiplier": 2.0},
    "滞納状況示唆_不思議な香りだ…（招待状：黒）": {"type": "exact_setting", "setting": 1, "value_multiplier": 5.0},
    "滞納状況示唆_君はなかなか": {"type": "exact_setting", "setting": 2, "value_multiplier": 5.0},
    "滞納状況示唆_君はなかなか…（本を良いね）": {"type": "exact_setting", "setting": 3, "value_multiplier": 5.0},
    "滞納状況示唆_僕としたことだがな": {"type": "exact_setting", "setting": 4, "value_multiplier": 5.0},
    "滞納状況示唆_存分に": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0},
    "滞納状況示唆_特別な夜を過ごし": {"type": "exact_setting", "setting": 6, "value_multiplier": 100.0},

    "AT終了画面_金木研（通常）": {"type": "normal"}, # 特になし、通常は尤度変更なし
    "AT終了画面_旧多二福（月）": {"type": "even_settings", "settings": [2, 4, 6], "value_multiplier": 5.0},
    "AT終了画面_アキラ（カネキ隣）": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0},
    "AT終了画面_ウタ（花）": {"type": "exact_setting", "setting": 6, "value_multiplier": 100.0},
    "AT終了画面_エト（集合）": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0},
    "AT終了画面_全員集合（アニメ2期最終話風）": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0},
    "AT終了画面_あんていく全員": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0},

    "エンディングカード_奇数設定示唆[弱]": {"type": "odd_settings", "settings": [1, 3, 5], "value_multiplier": 2.0, "exclude_multiplier": 0.5}, # 奇数でない場合に減らす倍率も設定
    "エンディングカード_奇数設定示唆[強]": {"type": "odd_settings", "settings": [1, 3, 5], "value_multiplier": 5.0, "exclude_multiplier": 0.1},
    "エンディングカード_偶数設定示唆[弱]": {"type": "even_settings", "settings": [2, 4, 6], "value_multiplier": 2.0, "exclude_multiplier": 0.5},
    "エンディングカード_偶数設定示唆[強]": {"type": "even_settings", "settings": [2, 4, 6], "value_multiplier": 5.0, "exclude_multiplier": 0.1},
    "エンディングカード_高設定示唆[弱]": {"type": "high_settings", "settings": [4, 5, 6], "value_multiplier": 2.0, "exclude_multiplier": 0.5},
    "エンディングカード_高設定示唆[強]": {"type": "high_settings", "settings": [4, 5, 6], "value_multiplier": 5.0, "exclude_multiplier": 0.1},
    "エンディングカード_設定1否定": {"type": "exclude_setting", "setting": 1, "value_multiplier": 1e-5}, # 否定の場合はほぼゼロ
    "エンディングカード_設定2否定": {"type": "exclude_setting", "setting": 2, "value_multiplier": 1e-5},
    "エンディングカード_設定3否定": {"type": "exclude_setting", "setting": 3, "value_multiplier": 1e-5},
    "エンディングカード_設定4否定": {"type": "exclude_setting", "setting": 4, "value_multiplier": 1e-5},
    "エンディングカード_設定5否定": {"type": "exclude_setting", "setting": 5, "value_multiplier": 1e-5},
    "エンディングカード_設定3以上濃厚": {"type": "min_setting", "setting": 3, "value_multiplier": 5.0},
    "エンディングカード_設定4以上濃厚": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0},
    "エンディングカード_設定5以上濃厚": {"type": "min_setting", "setting": 5, "value_multiplier": 50.0},
    "エンディングカード_設定6濃厚": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0},

    "獲得枚数表示_456 OVER": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0}, # 設定4以上濃厚
    "獲得枚数表示_666 OVER": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0}, # 設定6濃厚
    "獲得枚数表示_1000-7 OVER": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0}, # 設定6濃厚

    "ナミちゃんトロフィー_銅（700Gで確認）": {"type": "min_setting", "setting": 2, "value_multiplier": 5.0},
    "ナミちゃんトロフィー_銀": {"type": "min_setting", "setting": 3, "value_multiplier": 10.0},
    "ナミちゃんトロフィー_金": {"type": "min_setting", "setting": 4, "value_multiplier": 20.0},
    "ナミちゃんトロフィー_キリン": {"type": "min_setting", "setting": 5, "value_multiplier": 50.0},
    "ナミちゃんトロフィー_虹": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0},
}


# --- 推測ロジック関数 ---
def calculate_likelihood(observed_count, total_count, target_rate_value, is_probability_rate=True):
    """
    実測値と解析値から尤度を計算する。
    target_rate_value: 1/X形式の場合のX、または%形式の小数。
    is_probability_rate: Trueなら確率（%表示の小数）、Falseなら分母（1/XのX）
    """
    if total_count <= 0: # 試行回数がゼロ以下なら計算に影響を与えない
        return 1.0
    
    # 観測回数もゼロなら影響を与えない（データがないのと同じ）
    if observed_count <= 0 and total_count > 0:
        # ただし、解析値が0%なのに観測値が0なら尤度が高い
        if (is_probability_rate and target_rate_value == 0) or \
           (not is_probability_rate and target_rate_value == float('inf')): # 分母無限大=確率0
           return 1.0 # 観測0で解析値も0なら尤度高い

    if is_probability_rate: # %形式の確率の場合
        expected_value = total_count * target_rate_value
    else: # 1/X形式の分母の場合
        if target_rate_value == 0: # 分母が0はありえないが念のため
            return 1e-10 # 確率無限大になるので極めて低い尤度
        expected_value = total_count / target_rate_value
    
    # 期待値が0の場合
    if expected_value <= 1e-10: # 非常に小さい値で0とみなす
        return 1.0 if observed_count == 0 else 1e-10 # 期待値0で観測0なら尤度1、観測1以上ならほぼ0

    # ポアソン分布のPMF (確率質量関数) を使用して尤度を計算
    likelihood = poisson.pmf(observed_count, expected_value)
    
    # 尤度がゼロになることを避けるため、非常に小さい値を下限とする
    return max(likelihood, 1e-10) # 1e-10は0.0000000001


def predict_setting(data_inputs):
    overall_likelihoods = {setting: 1.0 for setting in range(1, 7)} # 各設定の総合尤度を1.0で初期化

    # データが一つも入力されていない場合のチェック
    any_data_entered = False
    for key, value in data_inputs.items():
        if isinstance(value, (int, float)):
            # 数値入力で0より大きい値があるか、または総ゲーム数などの分母情報か
            if value > 0 and key not in ['total_game_count', 'weak_cherry_count', 'cz_rem_total_count', 'cz_rize_total_count', 'reg_game_150g_total', 'pullback_total_count', 'ura_at_total_count', 'mental_stage_total_count']:
                any_data_entered = True
                break
            elif value > 0 and key in ['total_game_count', 'weak_cherry_count', 'cz_rem_total_count', 'cz_rize_total_count', 'reg_game_150g_total', 'pullback_total_count', 'ura_at_total_count', 'mental_stage_total_count']:
                any_data_entered = True # 分母の入力があればデータありとみなす
                break
    
    if not any_data_entered:
        return "データが入力されていません。推測を行うには、少なくとも1つの判別要素を入力してください。"

    # --- 確率系の要素の計算 ---

    # 総ゲーム数がないと計算できない項目
    total_game_count = data_inputs['total_game_count']
    
    # AT初当り確率
    if total_game_count > 0 and data_inputs['at_first_hit_count'] >= 0:
        for setting, rate_val in GAME_DATA["AT初当り確率"].items():
            likelihood = calculate_likelihood(data_inputs['at_first_hit_count'], total_game_count, rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood

    # CZ出現率トータル
    if total_game_count > 0 and data_inputs['cz_total_count'] >= 0:
        for setting, rate_val in GAME_DATA["CZ出現率トータル"].items():
            likelihood = calculate_likelihood(data_inputs['cz_total_count'], total_game_count, rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood

    # 各CZの当選率
    if data_inputs['cz_rem_total_count'] > 0 and data_inputs['cz_rem_observed_count'] >= 0:
        for setting, rate_val in GAME_DATA["CZ_レミニセンス当選率"].items():
            likelihood = calculate_likelihood(data_inputs['cz_rem_observed_count'], data_inputs['cz_rem_total_count'], rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood
    if data_inputs['cz_rize_total_count'] > 0 and data_inputs['cz_rize_observed_count'] >= 0:
        for setting, rate_val in GAME_DATA["CZ_大喰らいのリゼ当選率"].items():
            likelihood = calculate_likelihood(data_inputs['cz_rize_observed_count'], data_inputs['cz_rize_total_count'], rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood

    # 弱チェリーCZ当選率
    weak_cherry_count = data_inputs['weak_cherry_count']
    if weak_cherry_count > 0:
        if data_inputs['weak_cherry_cz_count_normal'] >= 0:
            for setting, rate_val in GAME_DATA["弱チェリーCZ当選率_通常滞在時"].items():
                likelihood = calculate_likelihood(data_inputs['weak_cherry_cz_count_normal'], weak_cherry_count, rate_val, is_probability_rate=True)
                overall_likelihoods[setting] *= likelihood
        if data_inputs['weak_cherry_cz_count_high'] >= 0:
             for setting, rate_val in GAME_DATA["弱チェリーCZ当選率_高確滞在時"].items():
                likelihood = calculate_likelihood(data_inputs['weak_cherry_cz_count_high'], weak_cherry_count, rate_val, is_probability_rate=True)
                overall_likelihoods[setting] *= likelihood

    # 規定ゲーム数150G以内CZ当選率 (発生回数と総試行回数)
    if data_inputs['reg_game_150g_total'] > 0 and data_inputs['reg_game_150g_count'] >= 0:
        for setting, rate_val in GAME_DATA["規定ゲーム数150G以内CZ当選率"].items():
            likelihood = calculate_likelihood(data_inputs['reg_game_150g_count'], data_inputs['reg_game_150g_total'], rate_val, is_probability_rate=True)
            overall_likelihoods[setting] *= likelihood

    # 下段リプレイ出現率
    if total_game_count > 0 and data_inputs['lower_replay_count'] >= 0:
        for setting, rate_val in GAME_DATA["下段リプレイ出現率"].items():
            likelihood = calculate_likelihood(data_inputs['lower_replay_count'], total_game_count, rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood

    # 初当りエピソードボーナス当選率
    if data_inputs['at_first_hit_count'] > 0 and data_inputs['ep_bonus_count'] >= 0:
        for setting, rate_val in GAME_DATA["初当りエピソードボーナス当選率"].items():
            likelihood = calculate_likelihood(data_inputs['ep_bonus_count'], data_inputs['at_first_hit_count'], rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood
            
    # 精神世界ステージ滞在G数振り分け (回数で評価)
    if data_inputs['mental_stage_total_count'] > 0:
        for setting in range(1, 7):
            setting_likelihood = 1.0
            total_obs = data_inputs['mental_stage_total_count']

            # 10G
            if data_inputs['mental_stage_10g_count'] >= 0:
                obs_10g = data_inputs['mental_stage_10g_count']
                expected_10g_rate = GAME_DATA["精神世界ステージ滞在G数_10G"][setting]
                setting_likelihood *= calculate_likelihood(obs_10g, total_obs, expected_10g_rate, is_probability_rate=True)
            # 20G
            if data_inputs['mental_stage_20g_count'] >= 0:
                obs_20g = data_inputs['mental_stage_20g_count']
                expected_20g_rate = GAME_DATA["精神世界ステージ滞在G数_20G"][setting]
                setting_likelihood *= calculate_likelihood(obs_20g, total_obs, expected_20g_rate, is_probability_rate=True)
            # 30G
            if data_inputs['mental_stage_30g_count'] >= 0:
                obs_30g = data_inputs['mental_stage_30g_count']
                expected_30g_rate = GAME_DATA["精神世界ステージ滞在G数_30G"][setting]
                setting_likelihood *= calculate_likelihood(obs_30g, total_obs, expected_30g_rate, is_probability_rate=True)
            
            overall_likelihoods[setting] *= setting_likelihood

    # 引き戻し（即前兆）確率 (回数で評価)
    if data_inputs['pullback_total_count'] > 0 and data_inputs['pullback_success_count'] >= 0:
        for setting, rate_val in GAME_DATA["引き戻し（即前兆）確率"].items():
            likelihood = calculate_likelihood(data_inputs['pullback_success_count'], data_inputs['pullback_total_count'], rate_val, is_probability_rate=True)
            overall_likelihoods[setting] *= likelihood

    # 裏AT当選率 (回数で評価)
    if data_inputs['ura_at_total_count'] > 0 and data_inputs['ura_at_success_count'] >= 0:
        for setting, rate_val in GAME_DATA["裏AT当選率_初当り経由"].items():
            likelihood = calculate_likelihood(data_inputs['ura_at_success_count'], data_inputs['ura_at_total_count'], rate_val, is_probability_rate=True)
            overall_likelihoods[setting] *= likelihood


    # --- 示唆系の要素の計算 ---
    # 各示唆が何回出たかをループで処理
    for hint_key, hint_info in HINT_DATA.items():
        observed_count = data_inputs.get(hint_key, 0) # 示唆の出現回数を取得

        if observed_count > 0: # 示唆が1回でも出現した場合のみ処理
            hint_type = hint_info["type"]
            
            for setting in range(1, 7):
                multiplier = 1.0 # その示唆によって尤度を増減させる倍率

                if hint_type == "even_settings": # 偶数設定示唆
                    if setting in hint_info["settings"]: # 偶数設定なら強くする
                        multiplier = hint_info.get("value_multiplier", 1.0)
                    else: # 奇数設定なら減らす
                        multiplier = hint_info.get("exclude_multiplier", 1e-3)
                elif hint_type == "odd_settings": # 奇数設定示唆
                    if setting in hint_info["settings"]: # 奇数設定なら強くする
                        multiplier = hint_info.get("value_multiplier", 1.0)
                    else: # 偶数設定なら減らす
                        multiplier = hint_info.get("exclude_multiplier", 1e-3)
                elif hint_type == "min_setting": # 設定X以上
                    if setting >= hint_info["setting"]: # X以上なら強くする
                        multiplier = hint_info.get("value_multiplier", 1.0)
                    else: # X未満なら減らす
                        multiplier = hint_info.get("exclude_multiplier", 1e-3)
                elif hint_type == "exact_setting": # 設定X確定/濃厚
                    if setting == hint_info["setting"]: # その設定なら強くする
                        multiplier = hint_info.get("value_multiplier", 1.0)
                    else: # その設定以外ならほぼゼロにする
                        multiplier = hint_info.get("exclude_multiplier", 1e-10) # 非常に小さい値
                elif hint_type == "exclude_setting": # 設定X否定
                    if setting == hint_info["setting"]: # 否定された設定ならほぼゼロにする
                        multiplier = hint_info.get("value_multiplier", 1e-10) # 否定のmultiplierとして使用
                    else: # 否定された設定以外なら尤度を維持
                        multiplier = hint_info.get("exclude_multiplier", 1.0) # 尤度を維持する倍率
                elif hint_type == "normal": # 特になし
                    multiplier = 1.0 # 尤度変更なし
                elif hint_type == "high_settings": # 高設定示唆 (設定4,5,6)
                    if setting in hint_info["settings"]: # 高設定なら強くする
                        multiplier = hint_info.get("value_multiplier", 1.0)
                    else: # 低設定なら減らす
                        multiplier = hint_info.get("exclude_multiplier", 1e-3)

                # 示唆の出現回数に応じて、尤度を適用
                # 例えば、1回出たら multiplier^1、2回出たら multiplier^2 と積算
                overall_likelihoods[setting] *= (multiplier ** observed_count)


    # --- 最終結果の処理 ---
    total_overall_likelihood_sum = sum(overall_likelihoods.values())
    if total_overall_likelihood_sum == 0: # 全ての尤度がゼロの場合
        return "データが不足しているか、矛盾しているため、推測が困難です。入力値を見直してください。"

    # 尤度を確率に正規化（合計が100%になるようにする）
    normalized_probabilities = {s: (p / total_overall_likelihood_sum) * 100 for s, p in overall_likelihoods.items()}

    # 最も確率の高い設定を見つける
    predicted_setting = max(normalized_probabilities, key=normalized_probabilities.get)
    max_prob_value = normalized_probabilities[predicted_setting]

    # 結果を整形して返す
    result_str = f"## ✨ 推測される設定: 設定{predicted_setting} (確率: 約{max_prob_value:.2f}%) ✨\n\n"
    result_str += "--- 各設定の推測確率 ---\n"
    # 確率が高い順にソートして表示
    for setting, prob in sorted(normalized_probabilities.items(), key=lambda item: item[1], reverse=True):
        result_str += f"  - 設定{setting}: 約{prob:.2f}%\n"

    return result_str


# --- Streamlit UI 部分 ---

st.set_page_config(
    page_title="東京喰種 設定推測ツール",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🎰 東京喰種 スロット設定推測ツール 🎰")

st.markdown(
    """
    このツールは、東京喰種の設定判別ツールです。通常時・AT中の様々な判別要素を総合的に判断し、
    台の設定（1〜6段階）を推測します。ご自身の遊技の参考に活用してみてください！
    """
)

# Sidebar for basic instructions
st.sidebar.title("使い方")
st.sidebar.markdown(
    """
    各項目で、ご自身で確認できたデータや示唆を入力してください。
    
    **数値入力項目**は、実測回数や総ゲーム数などを入力します。
    **示唆項目**は、出現した回数を入力します。
    
    入力が完了したら、一番下の「推測結果を表示」ボタンをクリックしてください。
    """
)

# --- 入力セクション ---
st.header("▼データ入力▼")

# --- 1. 基本データ ---
st.subheader("1. 基本データ (通常時・AT合算)")
col_g, col_cz, col_at = st.columns(3)
with col_g:
    total_game_count = st.number_input("総ゲーム数 (通常時+AT中)", min_value=0, value=0, key="total_game_count")
with col_cz:
    cz_total_count = st.number_input("CZ総回数", min_value=0, value=0, key="cz_total_count")
with col_at:
    at_first_hit_count = st.number_input("AT初当り回数 (CZ経由含む)", min_value=0, value=0, key="at_first_hit_count")

st.markdown("---")

# --- 2. 各CZの当選率 ---
st.subheader("2. 各CZの当選回数と分母")
st.markdown("※実測回数と試行ゲーム数を入力してください")
col_rem_val, col_rem_den = st.columns(2)
with col_rem_val:
    cz_rem_observed_count = st.number_input("レミニセンスCZ 当選回数", min_value=0, value=0, key="cz_rem_observed_count")
with col_rem_den:
    cz_rem_total_count = st.number_input("レミニセンスCZ 試行ゲーム数 (分母)", min_value=0, value=0, key="cz_rem_total_count")

col_rize_val, col_rize_den = st.columns(2)
with col_rize_val:
    cz_rize_observed_count = st.number_input("大喰らいのリゼCZ 当選回数", min_value=0, value=0, key="cz_rize_observed_count")
with col_rize_den:
    cz_rize_total_count = st.number_input("大喰らいのリゼCZ 試行ゲーム数 (分母)", min_value=0, value=0, key="cz_rize_total_count")

st.markdown("---")

# --- 3. 弱チェリーのCZ当選率 ---
st.subheader("3. 弱チェリーのCZ当選回数")
st.markdown("※弱チェリー総成立回数と、CZに当選した回数を入力してください")
weak_cherry_count = st.number_input("弱チェリー総成立回数", min_value=0, value=0, key="weak_cherry_count")
col_wc_norm, col_wc_high = st.columns(2)
with col_wc_norm:
    weak_cherry_cz_count_normal = st.number_input("└ 通常滞在時 CZ当選回数", min_value=0, value=0, key="weak_cherry_cz_count_normal")
with col_wc_high:
    weak_cherry_cz_count_high = st.number_input("└ 高確滞在時 CZ当選回数", min_value=0, value=0, key="weak_cherry_cz_count_high")

st.markdown("---")

# --- 4. 規定ゲーム数150G以内CZ当選率 ---
st.subheader("4. 規定ゲーム数150G以内CZ当選回数")
st.markdown("※150G以内のCZ当選回数と、その試行回数を入力してください")
col_reg_val, col_reg_den = st.columns(2)
with col_reg_val:
    reg_game_150g_count = st.number_input("150G以内CZ当選回数", min_value=0, value=0, key="reg_game_150g_count")
with col_reg_den:
    reg_game_150g_total = st.number_input("150G以内CZ当選試行回数 (例: CZ当選区間を150Gと数え、非当選区間も同様に150Gとして数える)", min_value=0, value=0, key="reg_game_150g_total")

st.markdown("---")

# --- 5. 下段リプレイの出現回数 ---
st.subheader("5. 下段リプレイの出現回数")
st.markdown("※総ゲーム数（上記1.で入力）と、下段リプレイの出現回数を入力してください")
lower_replay_count = st.number_input("下段リプレイ出現回数", min_value=0, value=0, key="lower_replay_count")

st.markdown("---")

# --- 6. 初当りエピソードボーナス当選回数 ---
st.subheader("6. 初当りエピソードボーナス当選回数")
st.markdown("※AT初当り回数（上記1.で入力）と、エピソードボーナス当選回数を入力してください")
ep_bonus_count = st.number_input("エピソードボーナス当選回数", min_value=0, value=0, key="ep_bonus_count")

st.markdown("---")

# --- 7. 精神世界ステージ滞在G数振り分け ---
st.subheader("7. 精神世界ステージ滞在G数振り分け")
st.markdown("※精神世界ステージに移行した総回数と、それぞれの滞在G数で終了した回数を入力してください")
mental_stage_total_count = st.number_input("精神世界ステージ移行総回数", min_value=0, value=0, key="mental_stage_total_count")
col_mental_10, col_mental_20, col_mental_30 = st.columns(3)
with col_mental_10:
    mental_stage_10g_count = st.number_input("└ 10G終了回数", min_value=0, value=0, key="mental_stage_10g_count")
with col_mental_20:
    mental_stage_20g_count = st.number_input("└ 20G終了回数", min_value=0, value=0, key="mental_stage_20g_count")
with col_mental_30:
    mental_stage_30g_count = st.number_input("└ 30G終了回数", min_value=0, value=0, key="mental_stage_30g_count")

st.markdown("---")

# --- 8. 引き戻し（即前兆）確率 ---
st.subheader("8. 引き戻し（即前兆）成功回数")
st.markdown("※引き戻しゾーン（即前兆）に移行した総回数と、引き戻し成功回数を入力してください")
col_pb_total, col_pb_success = st.columns(2)
with col_pb_total:
    pullback_total_count = st.number_input("引き戻しゾーン移行総回数", min_value=0, value=0, key="pullback_total_count")
with col_pb_success:
    pullback_success_count = st.number_input("引き戻し成功回数", min_value=0, value=0, key="pullback_success_count")

st.markdown("---")

# --- 9. 裏AT当選率 (初当り経由) ---
st.subheader("9. 裏AT当選回数 (初当り経由)")
st.markdown("※通常時からのAT初当り回数と、そのうち裏ATだった回数を入力してください")
col_ura_total, col_ura_success = st.columns(2)
with col_ura_total:
    ura_at_total_count = st.number_input("通常時からのAT初当り総回数", min_value=0, value=0, key="ura_at_total_count")
with col_ura_success:
    ura_at_success_count = st.number_input("裏ATスタート回数", min_value=0, value=0, key="ura_at_success_count")

st.markdown("---")

# --- 10. 示唆系の出現状況 (回数入力に修正) ---
st.subheader("10. 示唆系の出現回数")
st.markdown("※各示唆が出現した回数を入力してください。")

st.markdown("##### CZ失敗時カード")
cz_fail_card_suzuki_count = st.number_input("鈴屋什造（赤枠）出現回数", min_value=0, value=0, key="cz_fail_card_suzuki")
cz_fail_card_izumi_count = st.number_input("泉（金枠）出現回数", min_value=0, value=0, key="cz_fail_card_izumi")
cz_fail_card_arima_count = st.number_input("有馬貴将（虹枠）出現回数", min_value=0, value=0, key="cz_fail_card_arima")

st.markdown("##### 滞納状況示唆")
tainou_boku_dinner_count = st.number_input("「僕にはディナーでもどうだい？」出現回数", min_value=0, value=0, key="tainou_boku_dinner")
tainou_fushigi_kaori_count = st.number_input("「不思議な香りだ…（招待状：黒）」出現回数", min_value=0, value=0, key="tainou_fushigi_kaori")
tainou_kimi_nakanaka_count = st.number_input("「君はなかなか」出現回数", min_value=0, value=0, key="tainou_kimi_nakanaka")
tainou_kimi_nakanaka_hon_count = st.number_input("「君はなかなか…（本を良いね）」出現回数", min_value=0, value=0, key="tainou_kimi_nakanaka_hon")
tainou_boku_shitakoto_count = st.number_input("「僕としたことだがな」出現回数", min_value=0, value=0, key="tainou_boku_shitakoto")
tainou_zonbun_count = st.number_input("「存分に」出現回数", min_value=0, value=0, key="tainou_zonbun")
tainou_tokubetsu_yoru_count = st.number_input("「特別な夜を過ごし」出現回数", min_value=0, value=0, key="tainou_tokubetsu_yoru")

st.markdown("##### AT終了画面")
at_end_kinemoto_count = st.number_input("金木研（通常）出現回数", min_value=0, value=0, key="at_end_kinemoto")
at_end_futa_count = st.number_input("旧多二福（月）出現回数", min_value=0, value=0, key="at_end_futa")
at_end_akira_count = st.number_input("アキラ（カネキ隣）出現回数", min_value=0, value=0, key="at_end_akira")
at_end_uta_count = st.number_input("ウタ（花）出現回数", min_value=0, value=0, key="at_end_uta")
at_end_eto_count = st.number_input("エト（集合）出現回数", min_value=0, value=0, key="at_end_eto")
at_end_all_anime_count = st.number_input("全員集合（アニメ2期最終話風）出現回数", min_value=0, value=0, key="at_end_all_anime")
at_end_anteiku_count = st.number_input("あんていく全員出現回数", min_value=0, value=0, key="at_end_anteiku")

st.markdown("##### エンディング中のカード")
ending_card_kisu_w_count = st.number_input("奇数設定示唆[弱] 出現回数", min_value=0, value=0, key="ending_card_kisu_w")
ending_card_kisu_s_count = st.number_input("奇数設定示唆[強] 出現回数", min_value=0, value=0, key="ending_card_kisu_s")
ending_card_gusu_w_count = st.number_input("偶数設定示唆[弱] 出現回数", min_value=0, value=0, key="ending_card_gusu_w")
ending_card_gusu_s_count = st.number_input("偶数設定示唆[強] 出現回数", min_value=0, value=0, key="ending_card_gusu_s")
ending_card_kouset_w_count = st.number_input("高設定示唆[弱] 出現回数", min_value=0, value=0, key="ending_card_kouset_w")
ending_card_kouset_s_count = st.number_input("高設定示唆[強] 出現回数", min_value=0, value=0, key="ending_card_kouset_s")
ending_card_1hitei_count = st.number_input("設定1否定 出現回数", min_value=0, value=0, key="ending_card_1hitei")
ending_card_2hitei_count = st.number_input("設定2否定 出現回数", min_value=0, value=0, key="ending_card_2hitei")
ending_card_3hitei_count = st.number_input("設定3否定 出現回数", min_value=0, value=0, key="ending_card_3hitei")
ending_card_4hitei_count = st.number_input("設定4否定 出現回数", min_value=0, value=0, key="ending_card_4hitei")
ending_card_5hitei_count = st.number_input("設定5否定 出現回数", min_value=0, value=0, key="ending_card_5hitei")
ending_card_3ijou_count = st.number_input("設定3以上濃厚 出現回数", min_value=0, value=0, key="ending_card_3ijou")
ending_card_4ijou_count = st.number_input("設定4以上濃厚 出現回数", min_value=0, value=0, key="ending_card_4ijou")
ending_card_5ijou_count = st.number_input("設定5以上濃厚 出現回数", min_value=0, value=0, key="ending_card_5ijou")
ending_card_6noukou_count = st.number_input("設定6濃厚 出現回数", min_value=0, value=0, key="ending_card_6noukou")

st.markdown("##### 獲得枚数表示")
get_count_456_count = st.number_input("456 OVER 出現回数", min_value=0, value=0, key="get_count_456")
get_count_666_count = st.number_input("666 OVER 出現回数", min_value=0, value=0, key="get_count_666")
get_count_1000_7_count = st.number_input("1000-7 OVER 出現回数", min_value=0, value=0, key="get_count_1000_7")

st.markdown("##### ナミちゃんトロフィー")
nami_trophy_bronze_count = st.number_input("銅トロフィー出現回数", min_value=0, value=0, key="nami_trophy_bronze")
nami_trophy_silver_count = st.number_input("銀トロフィー出現回数", min_value=0, value=0, key="nami_trophy_silver")
nami_trophy_gold_count = st.number_input("金トロフィー出現回数", min_value=0, value=0, key="nami_trophy_gold")
nami_trophy_kirin_count = st.number_input("キリントロフィー出現回数", min_value=0, value=0, key="nami_trophy_kirin")
nami_trophy_rainbow_count = st.number_input("虹トロフィー出現回数", min_value=0, value=0, key="nami_trophy_rainbow")

st.markdown("---")

# --- 推測実行ボタン ---
if st.button("推測結果を表示"):
    # 全ての入力データを辞書にまとめる
    user_inputs = {
        'total_game_count': total_game_count,
        'cz_total_count': cz_total_count,
        'at_first_hit_count': at_first_hit_count,
        'cz_rem_observed_count': cz_rem_observed_count,
        'cz_rem_total_count': cz_rem_total_count,
        'cz_rize_observed_count': cz_rize_observed_count,
        'cz_rize_total_count': cz_rize_total_count,
        'weak_cherry_count': weak_cherry_count,
        'weak_cherry_cz_count_normal': weak_cherry_cz_count_normal,
        'weak_cherry_cz_count_high': weak_cherry_cz_count_high,
        'reg_game_150g_count': reg_game_150g_count,
        'reg_game_150g_total': reg_game_150g_total,
        'lower_replay_count': lower_replay_count,
        'ep_bonus_count': ep_bonus_count,
        'mental_stage_total_count': mental_stage_total_count,
        'mental_stage_10g_count': mental_stage_10g_count,
        'mental_stage_20g_count': mental_stage_20g_count,
        'mental_stage_30g_count': mental_stage_30g_count,
        'pullback_total_count': pullback_total_count,
        'pullback_success_count': pullback_success_count,
        'ura_at_total_count': ura_at_total_count,
        'ura_at_success_count': ura_at_success_count,
        
        # 示唆系データはキー名をHINT_DATAと一致させる
        "CZ失敗時カード_鈴屋什造（赤枠）": cz_fail_card_suzuki_count,
        "CZ失敗時カード_泉（金枠）": cz_fail_card_izumi_count,
        "CZ失敗時カード_有馬貴将（虹枠）": cz_fail_card_arima_count,

        "滞納状況示唆_僕にはディナーでもどうだい？": tainou_boku_dinner_count,
        "滞納状況示唆_不思議な香りだ…（招待状：黒）": tainou_fushigi_kaori_count,
        "滞納状況示唆_君はなかなか": tainou_kimi_nakanaka_count,
        "滞納状況示唆_君はなかなか…（本を良いね）": tainou_kimi_nakanaka_hon_count,
        "滞納状況示唆_僕としたことだがな": tainou_boku_shitakoto_count,
        "滞納状況示唆_存分に": tainou_zonbun_count,
        "滞納状況示唆_特別な夜を過ごし": tainou_tokubetsu_yoru_count,

        "AT終了画面_金木研（通常）": at_end_kinemoto_count,
        "AT終了画面_旧多二福（月）": at_end_futa_count,
        "AT終了画面_アキラ（カネキ隣）": at_end_akira_count,
        "AT終了画面_ウタ（花）": at_end_uta_count,
        "AT終了画面_エト（集合）": at_end_eto_count,
        "AT終了画面_全員集合（アニメ2期最終話風）": at_end_all_anime_count,
        "AT終了画面_あんていく全員": at_end_anteiku_count,

        "エンディングカード_奇数設定示唆[弱]": ending_card_kisu_w_count,
        "エンディングカード_奇数設定示唆[強]": ending_card_kisu_s_count,
        "エンディングカード_偶数設定示唆[弱]": ending_card_gusu_w_count,
        "エンディングカード_偶数設定示唆[強]": ending_card_gusu_s_count,
        "エンディングカード_高設定示唆[弱]": ending_card_kouset_w_count,
        "エンディングカード_高設定示唆[強]": ending_card_kouset_s_count,
        "エンディングカード_設定1否定": ending_card_1hitei_count,
        "エンディングカード_設定2否定": ending_card_2hitei_count,
        "エンディングカード_設定3否定": ending_card_3hitei_count,
        "エンディングカード_設定4否定": ending_card_4hitei_count,
        "エンディングカード_設定5否定": ending_card_5hitei_count,
        "エンディングカード_設定3以上濃厚": ending_card_3ijou_count,
        "エンディングカード_設定4以上濃厚": ending_card_4ijou_count,
        "エンディングカード_設定5以上濃厚": ending_card_5ijou_count,
        "エンディングカード_設定6濃厚": ending_card_6noukou_count,

        "獲得枚数表示_456 OVER": get_count_456_count,
        "獲得枚数表示_666 OVER": get_count_666_count,
        "獲得枚数表示_1000-7 OVER": get_count_1000_7_count,

        "ナミちゃんトロフィー_銅（700Gで確認）": nami_trophy_bronze_count,
        "ナミちゃんトロフィー_銀": nami_trophy_silver_count,
        "ナミちゃんトロフィー_金": nami_trophy_gold_count,
        "ナミちゃんトロフィー_キリン": nami_trophy_kirin_count,
        "ナミちゃんトロフィー_虹": nami_trophy_rainbow_count,
    }

    # 推測ロジックの実行と結果表示
    st.subheader("▼推測結果▼")
    result = predict_setting(user_inputs)
    st.markdown(result)