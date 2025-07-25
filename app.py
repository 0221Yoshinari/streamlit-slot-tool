import streamlit as st

# --- 定義データ ---
# 画像「テーブル選択率」のデータ（正確に入力してください）
# 設定3のデータは画像から読み取れなかったので仮で設定します。
TABLE_SELECTION_RATES = {
    1: {"テーブル1": 0.49, "テーブル2": 0.45, "テーブル3": 0.04, "テーブル4": 0.02},
    2: {"テーブル1": 0.37, "テーブル2": 0.54, "テーブル3": 0.03, "テーブル4": 0.06},
    3: {"テーブル1": 0.30, "テーブル2": 0.30, "テーブル3": 0.20, "テーブル4": 0.20}, # 仮の値
    4: {"テーブル1": 0.36, "テーブル2": 0.52, "テーブル3": 0.04, "テーブル4": 0.08},
    5: {"テーブル1": 0.52, "テーブル2": 0.36, "テーブル3": 0.08, "テーブル4": 0.04},
    6: {"テーブル1": 0.42, "テーブル2": 0.42, "テーブル3": 0.08, "テーブル4": 0.08},
}

# 画像「ステージのテーブル一覧」のデータ (3つの示唆が揃えば一意に特定できることを前提)
STAGE_TABLE_TO_HINT = {
    "テーブル1": {"AT開始時": "鳴海", "成功1回目": "勝", "成功2回目": "鳴海"},
    "テーブル2": {"AT開始時": "勝", "成功1回目": "鳴海", "成功2回目": "勝"},
    "テーブル3": {"AT開始時": "鳴海", "成功1回目": "勝", "成功2回目": "勝"},
    "テーブル4": {"AT開始時": "勝", "成功1回目": "鳴海", "成功2回目": "鳴海"},
}

# 示唆からテーブルへのマッピング（示唆単体の場合に利用）
INDIVIDUAL_HINT_TO_TABLES = {
    "AT開始時": {"鳴海": ["テーブル1", "テーブル3"], "勝": ["テーブル2", "テーブル4"]},
    "成功1回目": {"鳴海": ["テーブル2", "テーブル4"], "勝": ["テーブル1", "テーブル3"]},
    "成功2回目": {"鳴海": ["テーブル1", "テーブル4"], "勝": ["テーブル2", "テーブル3"]},
}

# --- 推測ロジック関数 ---
def predict_setting_multi_karakuri(all_at_data):
    overall_probabilities = {setting: 1.0 for setting in range(1, 7)} # 各設定の総合確率を1.0で初期化

    # データが一つも入力されていない場合のチェック
    any_data_entered = False
    for at_data in all_at_data:
        if at_data['start'] != "選択なし" or at_data['success1'] != "選択なし" or at_data['success2'] != "選択なし":
            any_data_entered = True
            break
    if not any_data_entered:
        return "データが入力されていません。推測を行うには、少なくとも1つのAT回で示唆を選択してください。"


    for at_data_idx, at_data in enumerate(all_at_data):
        start_hint = at_data['start']
        success1_hint = at_data['success1']
        success2_hint = at_data['success2']

        # このAT回で有効なデータが一つもない場合はスキップ
        if start_hint == "選択なし" and success1_hint == "選択なし" and success2_hint == "選択なし":
            continue

        for setting, rates in TABLE_SELECTION_RATES.items():
            current_at_prob_for_setting = 1.0 # このAT回における、その設定での確率

            # --- 3つの示唆が全て揃っている場合の処理 ---
            if (start_hint != "選択なし" and
                success1_hint != "選択なし" and
                success2_hint != "選択なし"):
                
                # 3つの示唆から一意のテーブルを特定するロジック
                identified_table = None
                for table_name, hints in STAGE_TABLE_TO_HINT.items():
                    if (hints["AT開始時"] == start_hint and
                        hints["成功1回目"] == success1_hint and
                        hints["成功2回目"] == success2_hint):
                        identified_table = table_name
                        break # 特定できたのでループを抜ける
                
                if identified_table: # 特定できた場合のみ確率を掛ける
                    current_at_prob_for_setting *= rates.get(identified_table, 0)
                else:
                    # 3つ揃ってもデータに一致しない場合は、その組み合わせの確率はゼロとして扱う。
                    current_at_prob_for_setting = 0.0


            # --- 示唆が全て揃っていない場合の処理 ---
            else:
                # AT開始時の示唆がある場合
                if start_hint != "選択なし":
                    sum_prob_for_start = 0.0
                    tables_for_hint = INDIVIDUAL_HINT_TO_TABLES["AT開始時"].get(start_hint, [])
                    for table in tables_for_hint:
                        sum_prob_for_start += rates.get(table, 0)
                    current_at_prob_for_setting *= sum_prob_for_start

                # 成功1回目の示唆がある場合
                if success1_hint != "選択なし":
                    sum_prob_for_success1 = 0.0
                    tables_for_hint = INDIVIDUAL_HINT_TO_TABLES["成功1回目"].get(success1_hint, [])
                    for table in tables_for_hint:
                        sum_prob_for_success1 += rates.get(table, 0)
                    current_at_prob_for_setting *= sum_prob_for_success1
                    
                # 成功2回目までの情報が揃わない状態で、成功2回目の示唆がある場合
                if success2_hint != "選択なし":
                    sum_prob_for_success2 = 0.0
                    tables_for_hint = INDIVIDUAL_HINT_TO_TABLES["成功2回目"].get(success2_hint, [])
                    for table in tables_for_hint:
                        sum_prob_for_success2 += rates.get(table, 0)
                    current_at_prob_for_setting *= sum_prob_for_success2

            # このAT回で計算された確率を総合確率に掛け合わせる
            overall_probabilities[setting] *= current_at_prob_for_setting


    # --- 最終結果の処理 ---
    total_overall_prob_sum = sum(overall_probabilities.values())
    if total_overall_prob_sum == 0:
        return "データが不足しているか、矛盾しているため、推測が困難です。入力値を見直してください。"

    # 尤度を確率に正規化（合計が100%になるようにする）
    normalized_probabilities = {s: (p / total_overall_prob_sum) * 100 for s, p in overall_probabilities.items()}

    # 最も確率の高い設定を見つける
    predicted_setting = max(normalized_probabilities, key=normalized_probabilities.get)
    max_prob_value = normalized_probabilities[predicted_setting]

    # 結果を整形して返す
    result_str = f"## ✨ 推測される設定: 設定{predicted_setting} (確率: 約{max_prob_value:.2f}%) ✨\n\n"
    result_str += "--- 各設定の推測確率 ---\n"
    for setting, prob in sorted(normalized_probabilities.items(), key=lambda item: item[1], reverse=True):
        result_str += f"  - 設定{setting}: 約{prob:.2f}%\n"

    return result_str

# --- Streamlit UI 部分 ---

st.set_page_config(
    page_title="からくりサーカス 設定推測ツール",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🎰 からくりサーカス スロット設定推測ツール 🎰")

st.markdown(
    """
    このツールは、からくりサーカスのステージ選択結果に基づいて、設定（1〜6）を推測します。
    ご自身の遊技の参考に活用してみてください！
    """
)

st.subheader("▼ステージごとのテーブル選択を入力▼")
st.markdown("データがない箇所は「選択なし」のままにしてください。")


all_at_inputs = [] # ユーザーの入力を格納するリスト
for i in range(1, 11): # 10回分のAT入力フォームを生成
    st.markdown(f"--- **AT {i}回目** ---")
    col1, col2, col3 = st.columns(3) # 3つのカラムに分割して表示

    with col1:
        at_start = st.selectbox(f"AT開始時 (AT{i})", ["選択なし", "鳴海", "勝"], key=f"start_{i}")
    with col2:
        at_success1 = st.selectbox(f"成功1回目 (AT{i})", ["選択なし", "鳴海", "勝"], key=f"success1_{i}")
    with col3:
        at_success2 = st.selectbox(f"成功2回目 (AT{i})", ["選択なし", "鳴海", "勝"], key=f"success2_{i}")
    
    all_at_inputs.append({
        'start': at_start,
        'success1': at_success1,
        'success2': at_success2
    })

st.markdown("---") # 区切り線

if st.button("推測結果を表示"):
    # 全ての入力データを辞書にまとめる
    # Streamlitの`selectbox`は選択された値を自動でstateとして保持するため、
    # `all_at_inputs`はボタンが押された時点での最新の状態を反映している
    
    st.subheader("▼推測結果▼")
    result = predict_setting_multi_karakuri(all_at_inputs)
    st.markdown(result)
