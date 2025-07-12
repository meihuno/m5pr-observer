import pandas as pd
from pathlib import Path

def main():
    pass

if __name__ == "__main__":
    
    # CSVのあるディレクトリを指定
    csv_dir = Path("./data_future/")  # ←ここを適宜変更してください

    # 空の辞書で {実験設定: {データ設定: 値}} を作る
    experiment_data = {}

    # すべての CSV ファイルを対象にする
    for file in csv_dir.glob("*.csv"):
        try:
            # ファイル名から設定を取得
            if 'lump_sum' in file.stem:
                experiment_setting, data_setting = file.stem.split("_sum_results_")
                if 'small_up' in data_setting:
                    continue
            else:
                data_setting, experiment_setting = file.stem.split("__")
        except ValueError:
            print(f"スキップ: ファイル名が不正 - {file.name}")
            continue

        print([data_setting, experiment_setting])

        # CSV 読み込み
        df = pd.read_csv(file)

        df['date'] = pd.to_datetime(df['investment_start_date'])
        df['profit'] = df['total_profit']

        # 日付フィルター（2025-07-07 〜 2025-12-18）
        start_date = pd.to_datetime("2025-07-07")
        end_date = pd.to_datetime("2025-12-18")

        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        # その期間の value の平均を計算
        average_value = filtered_df['profit'].mean()


        # 2025-07-07 のデータを抽出
        # row = df[df['date'] == pd.to_datetime("2025-07-07")]

        # if row.empty:
        #    print(f"スキップ: {file.name} に 2025-07-07 のデータなし")
        #    continue

        # value = row['profit'].values[0]
        value = df['profit'].mean()

        # 結果を辞書に格納
        if experiment_setting not in experiment_data:
            experiment_data[experiment_setting] = {}
        experiment_data[experiment_setting][data_setting] = average_value

    # DataFrame に変換（行：実験設定、列：データ設定）
    result_df = pd.DataFrame.from_dict(experiment_data, orient='index')
    result_df.index.name = "実験設定"

    # 結果表示
    print(result_df)

    # 必要なら CSV に保存
    result_df.to_csv("compare3.csv")