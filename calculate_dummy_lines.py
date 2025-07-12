from download_stock_info import DatabaseManager
from download_stock_info import IndexFetcher
from investment_calculator import InvestmentCalculator, StockData
from datetime import datetime, timedelta
import option_util as ou
import pandas as pd
import pprint as pp

def gogo_calculator(sp500_data, forex_data_dict, options, data_key, dir='data_future'):
        print(["Gogo", options])
        calculator = InvestmentCalculator(
            sp500_data=sp500_data, 
            forex_data=forex_data_dict, 
            verbose=True,**options
        )  
        profits = calculator.calculate_split_investment_profit(sp500_data)
        filename = calculator.filename
        # 各イテレーション終了時にCSVファイルに保存
        # 各イテレーション終了時にCSVファイルに保存
        profits.to_csv(f'{dir}/{data_key}__{filename}', index=False)
        print(f"{dir}/{data_key}__{filename} was saved")
        filename = f'{dir}/{filename}'
        return f"{data_key}__{filename}"

def ret_dummy_forex_data(filename):

    # CSV ファイルを読み込む
    df = pd.read_csv(filename)
    print(df.head())
    date_dict = {}
    for index, row in df.iterrows():
       date_str = row['Date']
       rate = row['Price']
       current_date = datetime.strptime(date_str, "%Y-%m-%d")
       key = current_date.strftime("%Y-%m-%d 00:00:00")
       date_dict[key] = {
            'date': current_date,
            'rate': rate,  # 初期値としてNoneを使用（必要に応じて変更）
            'dayofweek': current_date.weekday()  # 月曜=0, 日曜=6
        }
    return date_dict

def ret_dummy_stock_data(filename):

    # CSV ファイルを読み込む
    df = pd.read_csv(filename)
    print(df.head())
    date_dict = {}
    rows = []
    for index, row in df.iterrows():
       date_str = row['Date']
       current_date = datetime.strptime(date_str, "%Y-%m-%d")
       key = current_date.strftime("%Y-%m-%d 00:00:00")
       tmp_dict = {}
       tmp_dict['date'] = key
       tmp_dict['value'] = row['Price']
       tmp_dict['dayofweek'] = current_date.weekday()
       rows.append(tmp_dict)

    stock_data = [
        StockData(
            date=datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S'),
            price=float(row['value']),
            dayofweek=int(row['dayofweek'])
        )
        for row in rows  # SP500データの取得を想定
    ]
    return stock_data

if __name__ == "__main__":
    fetcher = IndexFetcher()
    index_data_list = fetcher.symbols

    forex_list = ["down", "same", "up"]
    score_list = ["down", "up", "v", "inverse_v"]

    index_key = "SP500"
    file_list = []
    for score_type1 in score_list:
        for forex_type1 in forex_list:

            forex_type = f"forex_{forex_type1}"
            forex_filename = f'dummy_lines/forex_{forex_type1}.csv'
            score_type = f"score_{score_type1}"
            score_filename = f'dummy_lines/sp500_{score_type1}.csv'

            forex_data_dict = ret_dummy_forex_data(forex_filename)
            stock_data = ret_dummy_stock_data(score_filename)
            data_key = f"{score_type}-{forex_type}"
            # 積み立て
            # 毎月6万で積み立て、マイナス5%ルールはなし。
            options = {
                "index_name": index_key,
                "nisa_monthly_investment": 60000, 
                "gogo_split": True,
                "gogo_m5pr": False,
                "m5pr_skip": True,
                "m5pr_skip_key": "slope",
                "gogo_year_first": False,
                "year_first_control":  'first_attack',
                "gogo_year_last_fire": False,
                "split_per_boost": False,
            }
            file = gogo_calculator(stock_data, forex_data_dict, options, data_key)
            file_list.append(file)
            
            #  年初一括
            options = {
                "index_name": index_key,
                "nisa_monthly_investment": 50000, 
                "gogo_split": False,
                "gogo_m5pr": False,
                "m5pr_skip": False,
                "m5pr_skip_key": "slope",
                "gogo_year_first": True,
                "gogo_year_last_fire": False,
                "split_per_boost": False,
            }
            
            file = gogo_calculator(stock_data, forex_data_dict, options, data_key)
            file_list.append(file)

            # 一括
            calculator = InvestmentCalculator(sp500_data=stock_data, forex_data=forex_data_dict, investment_period_year=15)
            profits = calculator.calculate_lump_sum_profit(stock_data)
            profits.to_csv(f'data_future/lump_sum_results_{score_type}-{forex_type}.csv', index=False)
            print(f'saving in data_future/lump_sum_results_{score_type}-{forex_type}.csv')

        pp.pprint(file_list)