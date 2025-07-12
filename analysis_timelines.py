import pandas as pd
from datetime import datetime
import option_util as ou

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

font_path = '/Users/sugihara/Library/Fonts/ipaexg.ttf'  # 適宜変更
import seaborn as sns

FONT_PROP = fm.FontProperties(fname=font_path)

class AnalysisTimeLines:
    def __init__(self, 
                 target='total_profit', 
                 index_name ="SP500", 
                 output_image_filename = './image/sp500_buypoint.png', 
                 show_minus_zone=True, 
                 show_sp500_line=False, 
                 show_forex_line=False
        ):
        self.index_name = index_name
        self.output_image_filename = output_image_filename
        self.data_dict = {}
        self.target = target
        self.show_minus_zone = show_minus_zone
        self.show_sp500_line = show_sp500_line
        self.show_forex_line = show_forex_line
        
        self.forex_list = []
        self.score_list = []

    def load_emax_csv(self, name='emaxis_slim', file_path='emaxslimsp500.utf8.csv'):
        """CSVファイルを読み込む"""        
        # file_path = file_path.replace('data/', 'data/')
        data = pd.read_csv(file_path)
        # 日付列を datetime 型に変換
        # data['date'] = pd.to_datetime(data['investment_start_date'])
        # data['date'] = pd.to_datetime(data['investment_end_date'])
        data['date'] = pd.to_datetime(data['基準日'])
        data['profit'] = data['基準価額（分配金再投資）(円)']

        initial_nav = 10038

        # 基準日（1行目）の指数と為替
        # 'sp500': "sp500.csv",
        # 'forex'
        df1 = self.data_dict['sp500']
        df1.set_index('date', inplace=True)
        df1 = df1[(df1.index >= '2018-07-03')]
        # base_sp500 = df1.loc[0, 'profit']
        
        df2 = self.data_dict['forex']
        df2.set_index('date', inplace=True)
        df2 = df2[(df2.index >= '2018-07-03')]
        df2 = df2.rename(columns={'profit': 'fx_score'})
        # base_fx = df2.loc[0, 'profit']

        df3 = pd.merge(df1, df2, on='date', how='inner')


        # 閾値となる日付
        threshold1 = pd.to_datetime('2021-01-01')  # ここを好きな日に変える
        threshold2 = pd.to_datetime('2023-01-01')  # ここを好きな日に変える
        threshold3 = pd.to_datetime('2024-01-01')  # ここを好きな日に変える

        def compute_nav(row):
            # print(row)
            if row['date'] >= threshold3:
                divisor = 27.0
            elif row['date'] >= threshold2:
                divisor = 28.0
            elif row['date'] >= threshold1:
                divisor = 29.0
            else:
                divisor = 30.0
            return (row['profit'] * ( row['fx_score']) ) / divisor

        # print(df3.head(10))
        df3 = df3.reset_index()
        df3['nav'] = df3.apply(compute_nav, axis=1)
        df3 = df3.set_index('date')
        # 割り算で nav 計算
        
        # df3['nav'] = (df3['profit'] * df3['fx_score']) / 30.0

        # 基準価額の推移を計算
        # data['nav'] = initial_nav * (df1['profit'] / base_sp500) * (df2['profit'] / base_fx)
        # data['nav'] = (df1['profit'] * df2['profit'] )
        #print(df1.head(10))
        #print(df2.head(10))
        print(df3.head(10))
        # print(data.head(10))
        self.data_dict[name] = data
        self.data_dict[name + '_omega'] = df3
        # exit()

    def load_csv(self, file_dict):
        """CSVファイルを読み込む"""
        for name, file_path in file_dict.items():
            # file_path = file_path.replace('data/', 'data/')
            data = pd.read_csv(file_path)
            # 日付列を datetime 型に変換
            # data['date'] = pd.to_datetime(data['investment_start_date'])
            # data['date'] = pd.to_datetime(data['investment_end_date'])
            if '_results.csv' in file_path:
                data['profit'] = data[self.target]
                data['date'] = pd.to_datetime(data['investment_start_date'])
                # data['date'] = pd.to_datetime(data['investment_end_date'])
            elif 'dummy_lines' in file_path:
                data['profit'] = data['Price']
                data['date'] = pd.to_datetime(data['Date'])
            else:
                data['date'] = pd.to_datetime(data['investment_start_date'])
                data['profit'] = data['total_profit']
            self.data_dict[name] = data
    
    def show_simple_line(self):
        df = self.data_dict['nikkei']
        df.set_index('investment_start_date', inplace=True)
        df = df[(df.index >= '1988-01-01')]
        df = df[(df.index < '1990-12-31')]
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['profit'], label='日経平均株価', color='blue')
        plt.title('日経平均株価の推移')
        plt.xlabel('日付')
        plt.ylabel('終値')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig('nikkei_line_short3.png', dpi=300, bbox_inches='tight')
        plt.show()
        

    def plot_profit_timeline(self, figsize=(12, 6)):
        """利益の時系列プロット"""
        if len(self.data_dict) == 0:
            raise ValueError("データが読み込まれていません。load_csv()を先に実行してください。")
            
        plt.figure(figsize=figsize)
        sns.set_style("whitegrid")
        
        # グラフのベース（左Y軸：株価）
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # 利益の時系列プロット
        #"""
        for name, data in self.data_dict.items():
            if name == 'sp500' or name == 'forex':
                continue
            # if 'm5pr' in name:
            #    color = 'red'
            #else:
            #    color = 'blue'
            # data.set_index('investment_end_date', inplace=True)
            # data = data[(data.index >= '2019-01-01')]
            # data = data[(data.index < '2025-12-31')]
            if name == 'alump':
                plt.plot(data['date'], data['profit'], 
                        # linewidth=0.5, color='#1f77b4')
                        linewidth=0.3, label=name, color='black')
            elif name == 'yearfirst':
                plt.plot(data['date'], data['profit'], 
                        # linewidth=0.5, color='#1f77b4')
                        linewidth=0.7, label=name, color='deeppink')
            elif name == 'emaxis_slim_omega':
                print(data.head(10))
                # plt.plot(data.index, data['nav'], linewidth=0.7, label=name, color='deeppink')
                plt.plot(data.index, data['nav'], 
                        # linewidth=0.5, color='#1f77b4')
                        linewidth=0.7, label="calculated_from_forex_and_sp500", color='deeppink')
            else:
                plt.plot(data['date'], data['profit'], 
                        # linewidth=0.5, color='#1f77b4')
                        linewidth=0.7, label=name)
        #"""
        plt.legend() 
        
        if self.show_sp500_line == True:
            df = self.data_dict['sp500']
            # 右Y軸（利益）
            print(df.head(10))
            
            #df.set_index('date', inplace=True)
            # dff = df[df.index >= '1996-10-30']
            # dff = df[df.index >= '1996-10-30']
            dff = df[df.index >= '2018-06-30']
            ax2 = ax1.twinx()
            ax2.plot(dff.index, dff['profit'], color='blue', label='SP500_Score', lw=0.3)
            ax2.set_ylabel('SP500_Score', color='blue')
            ax2.tick_params(axis='y', labelcolor='blue')

        if self.show_forex_line == True:
            df2 = self.data_dict['forex']
            # 右Y軸（利益）
            #df2.set_index('date', inplace=True)
            #dfff = df2[df2.index >= '1996-10-30']
            dfff = df2[df2.index >= '2018-06-30']
            ax3 = ax2.twinx()
            ax3.plot(dfff.index, dfff['profit'], color='green', label='為替レート', lw=0.3)
            ax3.set_ylabel('rate', color='green')
            ax3.tick_params(axis='y', labelcolor='green')

        def index_show_mode():
            # グラフの設定
            # plt.title(f'{self.index_name}投資の時系列収益（投資額1000万円）', fontsize=12, fontproperties=FONT_PROP)
            plt.title(f'SP500と為替レーとEMAXIS_SLIMSP500の値段', fontsize=12, fontproperties=FONT_PROP)
            plt.xlabel('投資開始日', fontsize=10, fontproperties=FONT_PROP)
            # plt.ylabel('利益（K万円）', fontsize=10, fontproperties=FONT_PROP)
            plt.ylabel('ドル円レート', fontsize=10, fontproperties=FONT_PROP)

        def future_index_show_mode():
            # グラフの設定
            # plt.title(f'{self.index_name}投資の時系列収益（投資額1000万円）', fontsize=12, fontproperties=FONT_PROP)
            plt.title(f'SP500の未来シミュレーション', fontsize=12, fontproperties=FONT_PROP)
            plt.xlabel('日付', fontsize=10, fontproperties=FONT_PROP)
            # plt.ylabel('利益（K万円）', fontsize=10, fontproperties=FONT_PROP)
            plt.ylabel('SP500スコア', fontsize=10, fontproperties=FONT_PROP)
        
        def future_forex_show_mode():
            # グラフの設定
            # plt.title(f'{self.index_name}投資の時系列収益（投資額1000万円）', fontsize=12, fontproperties=FONT_PROP)
            plt.title(f'ドル円レートの未来シミュレーション', fontsize=12, fontproperties=FONT_PROP)
            plt.xlabel('日付', fontsize=10, fontproperties=FONT_PROP)
            # plt.ylabel('利益（K万円）', fontsize=10, fontproperties=FONT_PROP)
            plt.ylabel('1ドルN円', fontsize=10, fontproperties=FONT_PROP)
        
        future_forex_show_mode()

        # x軸の日付表示を見やすく調整
        plt.xticks(rotation=45)
        
        # 利益がプラスとマイナスの領域で色分け
        # """
        if self.show_minus_zone == True:
            for name, data in self.data_dict.items():
                if name == 'sp500' or name == 'forex':
                    continue
                plt.axhline(y=0, color='r', linestyle='-', alpha=0.2)
                plt.fill_between(data['date'], data['profit'], 
                                where=(data['profit'] >= 0),
                                color='skyblue', alpha=0.3)
                plt.fill_between(data['date'], data['profit'], 
                                where=(data['profit'] < 0),
                                color='red', alpha=0.3)
        # """
        
        plt.tight_layout()
        plt.savefig(f'{self.output_image_filename}', dpi=300, bbox_inches='tight')
        plt.show()

    def show_summary_stats(self):
        """統計情報の表示"""
        """利益の時系列プロット"""
        if len(self.data_dict) == 0:
            raise ValueError("データが読み込まれていません。load_csv()を先に実行してください。")
        
        df_fx = self.data_dict['forex'] 
        df_fx = df_fx.rename(columns={"profit": "FX"})
        
        df_score = self.data_dict['sp500'] 
        df_score = df_score.rename(columns={"profit": "Stock"})
        
        for name, data in self.data_dict.items():
            print(f"=== {name} 統計情報 ===")
            print(f"データ期間: {data['date'].min().strftime('%Y-%m-%d')} から {data['date'].max().strftime('%Y-%m-%d')}")
            print(f"最大利益: {data['profit'].max():,.0f}円")
            print(f"最小利益: {data['profit'].min():,.0f}円")
            print(f"平均利益: {data['profit'].mean():,.0f}円")
            print("勝率: ", (data['profit'] > 0).mean())

            df_merged = data.merge(df_fx, on="date", how="left").merge(df_score, on="date", how="left")
            # print(df_merged)

            correlation_fx = df_merged["FX"].corr(df_merged["profit"])
            correlation_stock = df_merged["Stock"].corr(df_merged["profit"])

            print("為替と利益の相関係数:", correlation_fx)
            print("株価と利益の相関係数:", correlation_stock)

            # correlation_stock = data["Stock"].corr(df["Profit"])
            # correlation_fx = data["FX"].corr(df["Profit"])

    def show_summary_stats2(self):
        # データを読み込む
        # 利益の列を取り出す

        for name, data in self.data_dict.items():
            print(f"=== {name} 統計情報 ===")
            profits = data['profit']

            # 中央値
            median = profits.median()

            # 平均
            mean = profits.mean()

            # 標準偏差
            std_dev = profits.std()

            # 四分位範囲（IQR）
            q1 = profits.quantile(0.25)
            q3 = profits.quantile(0.75)
            iqr = q3 - q1

            # 結果表示
            print(f"中央値: {median:,.0f} 円")
            print(f"平均: {mean:,.0f} 円")
            print(f"標準偏差: {std_dev:,.0f} 円")
            print(f"IQR（四分位範囲）: {iqr:,.0f} 円（Q1={q1:,.0f}, Q3={q3:,.0f}）")


if __name__ == "__main__":
    
    args = ou.get_date_option()
    period = args.po
    # filename = 
    file_dict = {
        'alump': "investment_results1.csv",
        'split': "SP500_split_split_investment_results.csv",
        'splitm5pr': 'SP500_split-m5pr_split_investment_results.csv',
        'year': 'SP500_m5pr_year_split_investment_results.csv',
        'm5pr_only': 'SP500_m5pr_skip_skipsplit_investment_results.csv',
        'year_last_fire': 'SP500_m5pr_skip_fillinlast_skipsplit_investment_results.csv'
        }
    """
    file_dict = {
        "split10": "data/SP500_skip_skip_notfillin_split100000_investment_results.csv", 
        "split5": "data/SP500_skip_skip_notfillin_split50000_investment_results.csv", 
        "split5m5pr5": "data/SP500_m5pr50000_skip_notfillin_split50000_investment_results.csv", 
        "m5pr5": "data/SP500_m5pr50000_skip_notfillin_skipsplit_investment_results.csv", 
        "m5pr10": "data/SP500_m5pr100000_skip_notfillin_skipsplit_investment_results.csv", 
        "split10m5pr10": "data/SP500_m5pr100000_skip_notfillin_split100000_investment_results.csv", 
        "yearfirst": "data/SP500_skip_yearfirst_notfillin_skipsplit_investment_results.csv", 
        "split10yf": "data/SP500_skip_yearfirst_notfillin_split100000_investment_results.csv", 
        "split10m5prfill": "data/SP500_m5pr100000_skip_fillinlast_split100000_investment_results.csv", 
        'alump': 'data/lump_sum_results.csv'
    }
    """
    file_dict = {
        "split10": "data/SP500_skip_skip_notfillin_split100000_investment_results.csv", 
        #"split5": "data/SP500_skip_skip_notfillin_split50000_investment_results.csv", 
        "split5m5pr5": "data/SP500_m5pr50000_skip_notfillin_split50000_investment_results.csv", 
        # "m5pr5": "data/SP500_m5pr50000_skip_notfillin_skipsplit_investment_results.csv", 
        # "m5pr10": "data/SP500_m5pr100000_skip_notfillin_skipsplit_investment_results.csv", 
        "split10m5pr10": "data/SP500_m5pr100000_skip_notfillin_split100000_investment_results.csv", 
        "yearfirst": "data/SP500_skip_yearfirst_notfillin_skipsplit_investment_results.csv", 
        "split10yf": "data/SP500_skip_yearfirst_notfillin_split100000_investment_results.csv", 
        # "split10m5prfill": "data/SP500_m5pr100000_skip_fillinlast_split100000_investment_results.csv", 
        'alump': 'data/lump_sum_results.csv'
    }

    file_dict = {
        "split10": "data/NASDAQ100_skip_skip_notfillin_split100000_investment_results.csv", 
        #"split5": "data/SP500_skip_skip_notfillin_split50000_investment_results.csv", 
        "split5m5pr5": "data/NASDAQ100_m5pr50000_skip_notfillin_split50000_investment_results.csv", 
        # "m5pr5": "data/SP500_m5pr50000_skip_notfillin_skipsplit_investment_results.csv", 
        # "m5pr10": "data/SP500_m5pr100000_skip_notfillin_skipsplit_investment_results.csv", 
        "split10m5pr10": "data/NASDAQ100_m5pr100000_skip_notfillin_split100000_investment_results.csv", 
        "yearfirst": "data/NASDAQ100_skip_yearfirst_notfillin_skipsplit_investment_results.csv", 
        "split10yf": "data/NASDAQ100_skip_yearfirst_notfillin_split100000_investment_results.csv", 
        # "split10m5prfill": "data/SP500_m5pr100000_skip_fillinlast_split100000_investment_results.csv", 
        'alump': 'data/lump_sum_results.csv'
    }

    file_dictN = {
        "split10": "data/NIKKEI225_skip_skip_notfillin_split100000_investment_results.csv", 
        "split5": "data/NIKKEI225_skip_skip_notfillin_split50000_investment_results.csv", 
        "split5m5pr5": "data/NIKKEI225_m5pr50000_skip_notfillin_split50000_investment_results.csv", 
        "mpr5": "data/NIKKEI225_m5pr50000_skip_notfillin_skipsplit_investment_results.csv", 
        "m5pr10": "data/NIKKEI225_m5pr100000_skip_notfillin_skipsplit_investment_results.csv", 
        "split10m5pr10": "data/NIKKEI225_m5pr100000_skip_notfillin_split100000_investment_results.csv", 
        "yearfirst": "data/NIKKEI225_skip_yearfirst_notfillin_skipsplit_investment_results.csv", 
        "split10yf": "data/NIKKEI225_skip_yearfirst_notfillin_split100000_investment_results.csv", 
        #"split10m5prfill": "data/NIKKEI225_skip_yearfirst_notfillin_split100000_investment_results.csv", 
        "alump": "data/NIKKEI225_m5pr100000_skip_fillinlast_split100000_investment_results.csv", 
        # 'nikkei': "nikkei.csv",
    }

    file_dict2 = {
        #"split10": "data/SP500_skip_skip_notfillin_split100000_investment_results.csv", 
        "split5": "data/SP500_skip_m5pr-not-skip_skip_notfillin_split50000_investment_results.csv", 
        "split5-per-boost": "data/SP500_skip_m5pr-not-skip_skip_notfillin_split-boost-50000_investment_results.csv",
        #"split5m5pr5": "data/SP500_m5pr50000_skip_notfillin_split50000_investment_results.csv", 
        "m5pr5": "data/SP500_m5pr50000_m5pr-not-skip_skip_notfillin_skipsplit_investment_results.csv", 
        "m5pr5-skip": "data/SP500_m5pr50000_m5pr-skip50000_skip_notfillin_skipsplit_investment_results.csv",
        "m5pr5-dayskip": "data/SP500_m5pr50000_m5pr-day-skip50000_skip_notfillin_skipsplit_investment_results.csv",
        "m5pr5-slope": "data/SP500_m5pr50000_m5pr-slope-skip50000_skip_notfillin_skipsplit_investment_results.csv",
        "m5pr5-per30": "data/SP500_m5pr50000_m5pr-per-skip50000_skip_notfillin_skipsplit_investment_results.csv",
        "m5pr-boost": "data/SP500_m5pr50000_m5pr-slope-boost-skip50000_skip_notfillin_skipsplit_investment_results.csv",

        # "m5pr10": "data/SP500_m5pr100000_skip_notfillin_skipsplit_investment_results.csv", 
        # "split10m5pr10": "data/SP500_m5pr100000_skip_notfillin_split100000_investment_results.csv", 
        # "yearfirst": "data/SP500_skip_yearfirst_notfillin_skipsplit_investment_results.csv", 
        # "split10yf": "data/SP500_skip_yearfirst_notfillin_split100000_investment_results.csv", 
        # "split10m5prfill": "data/SP500_m5pr100000_skip_fillinlast_split100000_investment_results.csv", 
        # 'alump': 'data/lump_sum_results.csv'
        'sp500': "sp500.csv",
    }

    file_dict = { 
        "m5pr5": "data/SP500_m5pr50000_m5pr-gogo_yf-skip_notfillin_split-skip_investment_results.csv", 
        "m5pr5_slope": "data/SP500_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        "m5pr5_day": "data/SP500_m5pr50000_m5pr50000-day-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        "m5pr5_per": "data/SP500_m5pr50000_m5pr50000-per-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        "split5": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split50000_investment_results.csv", 
        "split10": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split100000_investment_results.csv", 
        "split5per": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split50000-per30-boost_investment_results.csv", 
        "split10per": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split100000-per30-boost_investment_results.csv", 
        "split5per+m5pr_slope": "data/SP500_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split50000-per30-boost_investment_results.csv", 
        "split10per+m5pr_slope": "data/SP500_m5pr100000_m5pr100000-slope-skip_yf-skip_notfillin_split100000-per30-boost_investment_results.csv", 
        "split5+m5pr": "data/SP500_m5pr50000_m5pr-gogo_yf-skip_notfillin_split50000_investment_results.csv", 
        "split5+m5pr_slope": "data/SP500_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split50000_investment_results.csv", 
        "split10+m5pr": "data/SP500_m5pr100000_m5pr-gogo_yf-skip_notfillin_split100000_investment_results.csv", 
        "split10+m5pr_slope": "data/SP500_m5pr100000_m5pr100000-slope-skip_yf-skip_notfillin_split100000_investment_results.csv", 
        "yearfirst": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst-normal_notfillin_split-skip_investment_results.csv", 
        "yearfirst-fa": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst-first_attack_notfillin_split-skip_investment_results.csv",
        "yearfirst+split5": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst_notfillin_split50000_investment_results.csv", 
        "yearfirst+split10": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst_notfillin_split100000_investment_results.csv",
        'alump': 'data/lump_sum_results.csv',
        'sp500': "sp500.csv",
    }
    file_dict = {
        
        "m5pr5": "data/SP500_m5pr50000_m5pr-gogo_yf-skip_notfillin_split-skip_investment_results.csv", 
        # "m5pr5_slope": "data/SP500_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        # "m5pr5_day": "data/SP500_m5pr50000_m5pr50000-day-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        # "m5pr5_per": "data/SP500_m5pr50000_m5pr50000-per-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        
        "split5": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split50000_investment_results.csv", 
        "split10": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split100000_investment_results.csv", 
        "split5per": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split50000-per30-boost_investment_results.csv", 
        # "split10per": "data/SP500_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split100000-per30-boost_investment_results.csv", 
        "split5per+m5pr_slope": "data/SP500_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split50000-per30-boost_investment_results.csv", 
        #"split10per+m5pr_slope": "data/SP500_m5pr100000_m5pr100000-slope-skip_yf-skip_notfillin_split100000-per30-boost_investment_results.csv", 
        "split5+m5pr": "data/SP500_m5pr50000_m5pr-gogo_yf-skip_notfillin_split50000_investment_results.csv", 
        "split5+m5pr_slope": "data/SP500_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split50000_investment_results.csv", 
        
        #"split10+m5pr": "data/SP500_m5pr100000_m5pr-gogo_yf-skip_notfillin_split100000_investment_results.csv", 
        # "split10+m5pr_slope": "data/SP500_m5pr100000_m5pr100000-slope-skip_yf-skip_notfillin_split100000_investment_results.csv", 
        "yearfirst": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst-normal_notfillin_split-skip_investment_results.csv", 
        # "yearfirst-fa": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst-first_attack_notfillin_split-skip_investment_results.csv",
        # "yearfirst+split5": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst_notfillin_split50000_investment_results.csv", 
        # "yearfirst+split10": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst_notfillin_split100000_investment_results.csv",
        'alump': 'data/lump_sum_results.csv',
        'sp500': "sp500.csv",
        'forex': 'forex_data.csv'
    }

    file_dictN = {
        # "m5pr5": "dataN/NIKKEI225_m5pr50000_m5pr-gogo_yf-skip_notfillin_split-skip_investment_results.csv", 
        # "m5pr5_slope": "dataN/NIKKEI225_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        # "m5pr5_day": "dataN/NIKKEI225_m5pr50000_m5pr50000-day-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        # "m5pr5_slopeday": "dataN/NIKKEI225_m5pr50000_m5pr50000-slopeday-skip_yf-skip_notfillin_split-skip_investment_results.csv",
        # "m5pr5_per": "dataN/NIKKEI225_m5pr50000_m5pr50000-per-skip_yf-skip_notfillin_split-skip_investment_results.csv", 
        # "split5": "dataN/NIKKEI225_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split50000_investment_results.csv", 
        # "split10": "dataN/NIKKEI225_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split100000_investment_results.csv", 
        # "split5per": "dataN/NIKKEI225_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split50000-per30-boost_investment_results.csv", 
        #"split10per": "dataN/NIKKEI225_m5pr-skip_m5pr-gogo_yf-skip_notfillin_split100000-per30-boost_investment_results.csv", 
        #"split5per+m5pr_slope": "dataN/NIKKEI225_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split50000-per30-boost_investment_results.csv", 
        #"split10per+m5pr_slope": "dataN/NIKKEI225_m5pr100000_m5pr100000-slope-skip_yf-skip_notfillin_split100000-per30-boost_investment_results.csv", 
        # "split5+m5pr": "dataN/NIKKEI225_m5pr50000_m5pr-gogo_yf-skip_notfillin_split50000_investment_results.csv", 
        # "split5+m5pr_slope": "dataN/NIKKEI225_m5pr50000_m5pr50000-slope-skip_yf-skip_notfillin_split50000_investment_results.csv", 
        #"split10+m5pr": "dataN/NIKKEI225_m5pr100000_m5pr-gogo_yf-skip_notfillin_split100000_investment_results.csv", 
        #"split10+m5pr_slope": "dataN/NIKKEI225_m5pr100000_m5pr100000-slope-skip_yf-skip_notfillin_split100000_investment_results.csv", 
        # "yearfirst": "dataN/NIKKEI225_m5pr-skip_m5pr-gogo_yearfirst-normal_notfillin_split-skip_investment_results.csv", 
        #"yearfirst-fa": "dataN/NIKKEI225_m5pr-skip_m5pr-gogo_yearfirst-first_attack_notfillin_split-skip_investment_results.csv",
        #"yearfirst+split5": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst_notfillin_split50000_investment_results.csv", 
        #"yearfirst+split10": "data/SP500_m5pr-skip_m5pr-gogo_yearfirst_notfillin_split100000_investment_results.csv",
        # 'alump': 'dataN/lump_sum_results.csv',
        'sp500': "sp500.csv",
        'forex': 'forex_data.csv'
    }

    file_dictIndex = {
        # 'sp500': "sp500.csv",
        # 'forex': 'forex_data.csv',
        'nikkei': "nikkei225.csv"
    }
    file_dict_sp500 = {
    "sp500_down": "dummy_lines/sp500_down.csv", 
    "sp500_inverse_v": "dummy_lines/sp500_inverse_v.csv",
    "sp500_up":"dummy_lines/sp500_up.csv",
    "sp500_v": "dummy_lines/sp500_v.csv"
    }

    file_dict_forex = {
        "forex_down": "dummy_lines/forex_down.csv",
        "forex_same": "dummy_lines/forex_same.csv",      
        "forex_up": "dummy_lines/forex_up.csv"
    }

    box = AnalysisTimeLines(show_minus_zone=False, target='final_buy_point', output_image_filename='./image/emaxis_slim2.png', show_sp500_line=True, show_forex_line=True)
    # box = AnalysisTimeLines(show_minus_zone=True, index_name='日経255', output_image_filename='./image/n255_m5pr_exp.png', show_sp500_line=False, show_forex_line=False)
    # box = AnalysisTimeLines(show_minus_zone=False, index_name='SP500', output_image_filename='./image/forex_future_dummy.png', show_sp500_line=False, show_forex_line=False)
    box.load_csv(file_dictN)
    box.load_emax_csv(name='emaxis_slim', file_path='emaxislimsp500.utf8.csv')
    # box.show_simple_line()
    # exit()
    
    # box.show_summary_stats()
    # box.show_summary_stats2()
    box.plot_profit_timeline()