from download_stock_info import DatabaseManager
from download_stock_info import IndexFetcher
from investment_calculator import InvestmentCalculator, StockData
from datetime import datetime, timedelta
import option_util as ou
import pandas as pd

def gogo_calculator(sp500_data, forex_data_dict, options, dir='data'):
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
        profits.to_csv(f'{dir}/{filename}', index=False)
        print(f"{dir}/{filename} was saved")
        filename = f'{dir}/{filename}'
        return filename

def ret_dummy_forex_data(rate):

    start_date = datetime(1925, 10, 31)
    end_date = datetime(2025,5,25)
    # end_date = datetime(2025,5,17)
    # end_date = datetime.now() #.date()
    # 辞書の作成
    date_dict = {}

    current_date = start_date
    while current_date <= end_date:
        rate = rate
        key = current_date.strftime("%Y-%m-%d 00:00:00")
        date_dict[key] = {
            'date': current_date,
            'rate': rate,  # 初期値としてNoneを使用（必要に応じて変更）
            'dayofweek': current_date.weekday()  # 月曜=0, 日曜=6
        }
        current_date += timedelta(days=1)
    
    return date_dict

def save_forex_date(forex_data_dict):
    # 辞書の値部分だけをDataFrameに変換
    df = pd.DataFrame(forex_data_dict.values())

    # 必要であれば日付を文字列に変換（例：YYYY-MM-DD）
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df = df.drop_duplicates(subset='date', keep='first')
    df = df.sort_values(by='date')
    new_df = df.rename(columns={'date': 'investment_start_date', 'rate': 'total_profit'})
    # CSVに出力
    new_df.to_csv('forex_data.csv', index=False)

if __name__ == "__main__":
    fetcher = IndexFetcher()
    index_data_list = fetcher.symbols

    db_manager = DatabaseManager()
    args = ou.get_date_option()
    period = args.po
    update_forex = args.upforex
    
    index_key = 'SP500'
    # index_key = 'NASDAQ100'
    # index_key = 'NIKKEI225'

    print(f"forex update {update_forex}")
    if update_forex:
        db_manager.upload_forex_data(period=period)
    
    rows = db_manager.get_all_period(index_key)
    file_list = []
    # DataFrameに変換
    df = pd.DataFrame(rows)
    new_df = df.rename(columns={'date': 'investment_start_date', 'value': 'total_profit'})

    if index_key == 'NIKKEI225':
        forex_data_dict = ret_dummy_forex_data(1.0)
        new_df.to_csv('nikkei225.csv', index=False, encoding='utf-8')
    elif index_key == 'SP500':
        forex_data_dict = db_manager.get_forex_data()
        # CSVファイルに保存（UTF-8）
        new_df.to_csv('sp500.csv', index=False, encoding='utf-8')
    elif index_key == 'NASDAQ100':
        pass
        # not implemented
    # for k,v in forex_data_dict.items():
    # print(f"為替データ: {k} = {v['rate']:.3f} ({v['date']})")
    # save_forex_date(forex_data_dict)
    # exit()
    exit()
    
    print(f"Start {index_key}")

    # SP500/nasdaq100データを StockData オブジェクトのリストに変換
    stock_data = [
        StockData(
            date=datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S'),
            price=float(row['value']),
            dayofweek=int(row['dayofweek'])
        )
        for row in rows  # SP500データの取得を想定
    ]
    
    # """
    # 毎月5万で積み立て、マイナス5%ルールはなし。
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": True,
        "gogo_m5pr": True,
        "m5pr_skip": True,
        "m5pr_skip_key": "slope",
        "gogo_year_first": False,
        "year_first_control":  'first_attack',
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)
    #"""
    exit()
    
    # 毎月5万で積み立てskip、マイナス5%ルールのみ。
    # day rangeによるskip
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "m5pr_skip": True,
        "m5pr_skip_key": "slopeday",
        "gogo_split": False,
        "gogo_m5pr": True,
        "gogo_year_first": False,
        "gogo_year_last_fire": False
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)
    exit()

    # 毎月5万で積み立てskip、マイナス5%ルールのみ。
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "m5pr_skip": False,
        "gogo_split": False,
        "gogo_m5pr": True,
        "gogo_year_first": False,
        "gogo_year_last_fire": False
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)
    # exit()

    # 毎月5万で積み立てskip、マイナス5%ルールのみ。
    # slopeによるskip
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "m5pr_skip": True,
        "m5pr_skip_key": "slope",
        "gogo_split": False,
        "gogo_m5pr": True,
        "gogo_year_first": False,
        "gogo_year_last_fire": False
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月5万で積み立てskip、マイナス5%ルールのみ。
    # day rangeによるskip
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "m5pr_skip": True,
        "m5pr_skip_key": "day",
        "gogo_split": False,
        "gogo_m5pr": True,
        "gogo_year_first": False,
        "gogo_year_last_fire": False
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月5万で積み立てskip、マイナス5%ルールのみ。
    # per によるskip
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "m5pr_skip": True,
        "m5pr_skip_key": "per",
        "gogo_split": False,
        "gogo_m5pr": True,
        "gogo_year_first": False,
        "gogo_year_last_fire": False
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)
    
    # exit()

    # 毎月5万は、他はしない。
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": True,
        "gogo_m5pr": False,
        "gogo_year_first": False,
        "gogo_year_last_fire": False
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月10万は、他はしない。
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 100000, 
        "gogo_split": True,
        "gogo_m5pr": False,
        "gogo_year_first": False,
        "gogo_year_last_fire": False
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月5万は、PER boost。
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": True,
        "gogo_m5pr": False,
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": True,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月10万は、PER boost。
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 100000, 
        "gogo_split": True,
        "gogo_m5pr": False,
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": True,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月5万は、PER boost。m5pr rule slope skip
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": True,
        "gogo_m5pr": True,
        "m5pr_skip": True,
        "m5pr_skip_key": "slope",
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": True,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月10万は、PER boost。m5pr rule slope skip

    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 100000, 
        "gogo_split": True,
        "gogo_m5pr": True,
        "m5pr_skip": True,
        "m5pr_skip_key": "slope",
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": True,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月5万は、m5pr rule 
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": True,
        "gogo_m5pr": True,
        "m5pr_skip": False,
        "m5pr_skip_key": "slope",
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月5万は、m5pr rule、slope skip
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": True,
        "gogo_m5pr": True,
        "m5pr_skip": True,
        "m5pr_skip_key": "slope",
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月10万は、m5pr rule 
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 100000, 
        "gogo_split": True,
        "gogo_m5pr": True,
        "m5pr_skip": False,
        "m5pr_skip_key": "slope",
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 毎月10万は、m5pr rule、slope skip
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 100000, 
        "gogo_split": True,
        "gogo_m5pr": True,
        "m5pr_skip": True,
        "m5pr_skip_key": "slope",
        "gogo_year_first": False,
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
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
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    #  年初一括 first attack
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": False,
        "gogo_m5pr": False,
        "m5pr_skip": False,
        "m5pr_skip_key": "slope",
        "gogo_year_first": True,
        "year_first_control":  'first_attack',
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    #  年初一括 + 5万積み立て
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 50000, 
        "gogo_split": True,
        "gogo_m5pr": False,
        "m5pr_skip": False,
        "m5pr_skip_key": "slope",
        "gogo_year_first": True,
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    #  年初一括 + 10万積み立て
    options = {
        "index_name": index_key,
        "nisa_monthly_investment": 100000, 
        "gogo_split": True,
        "gogo_m5pr": False,
        "m5pr_skip": False,
        "m5pr_skip_key": "slope",
        "gogo_year_first": True,
        "gogo_year_last_fire": False,
        "split_per_boost": False,
    }
    file = gogo_calculator(stock_data, forex_data_dict, options)
    file_list.append(file)

    # 一括
    calculator = InvestmentCalculator(sp500_data=stock_data, forex_data=forex_data_dict)
    profits = calculator.calculate_lump_sum_profit(stock_data)
    profits.to_csv('dataN/lump_sum_results.csv', index=False)
    
    for fidx, filename in enumerate(file_list):
        print(f'  "{fidx}": "{filename}", ')

    db_manager.close()