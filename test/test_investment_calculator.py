# test/test_database_manager.py
"""リファクタリング時にテストを追加です。
"""
import unittest
import sys
import os
from datetime import datetime, timedelta
import math

# カレントディレクトリをsys.pathに追加してインポート可能にする
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download_stock_info import IndexFetcher, DatabaseManager  # カレントディレクトリのモジュールをインポート
from download_stock_info import DatabaseManager
from download_stock_info import IndexFetcher
from investment_calculator import InvestmentCalculator, StockData
from datetime import datetime
import option_util as ou

class TestInvestmentCalculator(unittest.TestCase):
    
    def setUp(self):
        # テストケースごとに初期化処理が必要な場合に記述（任意）
        self.fetcher = IndexFetcher()
        self.db_manager = DatabaseManager()
        self.investment_limit =  10000000
        self.nisa_investment = 2400000
        self.nisa_taxable = 7600000

        self.forex_data_dict = self._ret_forex_data()
        self.sp500_data = self._ret_stock_data()
        pass
    
    def _ret_stock_data(self):
        start_date = datetime(1996, 10, 31)
        end_date = datetime(2025,4,29)
        
        sp500_data = []
        current_date = start_date
        while current_date <= end_date:
            
            if current_date.strftime("%Y-%m-%d 00:00:00") == start_date.strftime("%Y-%m-%d 00:00:00"):
                price = 10000
            elif current_date.strftime("%Y-%m-%d 00:00:00") == end_date.strftime("%Y-%m-%d 00:00:00"):
                price = 10000
            else:
                price = 5000
            stock = StockData(
                date=current_date,
                price=price,  # データがあればここに埋める
                dayofweek=current_date.weekday()
            )
            sp500_data.append(stock)
            current_date += timedelta(days=1)

        return sp500_data

    def _ret_forex_data(self):

        start_date = datetime(1996, 10, 31)
        end_date = datetime(2025,4,29)

        # 辞書の作成
        date_dict = {}

        current_date = start_date
        while current_date <= end_date:
            if current_date.strftime("%Y-%m-%d 00:00:00") == end_date.strftime("%Y-%m-%d 00:00:00"):
                rate = 50.0
            else:
                rate = 100.0
            key = current_date.strftime("%Y-%m-%d 00:00:00")
            date_dict[key] = {
                'date': current_date,
                'rate': rate,  # 初期値としてNoneを使用（必要に応じて変更）
                'dayofweek': current_date.weekday()  # 月曜=0, 日曜=6
            }
            current_date += timedelta(days=1)
        
        return date_dict

    def test_calculate_split_profit(self):

        calculator = InvestmentCalculator(
            sp500_data = self.sp500_data, 
            forex_data = self.forex_data_dict, 
            gogo_split = True, 
            gogo_m5pr = False
        )
        # profits = calculator.calculate_split_investment_profit(sp500_data)
        profits = calculator.calculate_split_investment_profit(self.sp500_data)
        
        # 最後の5件を取得・表示
        last_five = list(self.forex_data_dict.items())[-5:]
        for key, value in last_five:
            print(key, value)
        
        for data1 in self.sp500_data[-5:]:
            print(data1)
        
        print(profits.head(10))
        print([profits.tail(20)])
                
        # 240が240になった。出費は240。もうけは0.0
        exp_score0 = 0.0
        for idx in profits.index[1:-3]:
            target_profit = profits.at[idx, 'total_profit']
            print([idx, target_profit])
            check = math.isclose(target_profit, exp_score0, abs_tol = 1e-8)
            self.assertEqual(check, True, f"Row {idx} is not '0.0'")

    def test_calculate_m5pr_split_profit(self):

        calculator = InvestmentCalculator(
            sp500_data = self.sp500_data, 
            forex_data = self.forex_data_dict, 
            gogo_split = True, 
            gogo_m5pr = True,
            gogo_year_first = False,
            gogo_year_last_fire = False
        )
        # profits = calculator.calculate_split_investment_profit(sp500_data)
        profits = calculator.calculate_split_investment_profit(self.sp500_data)
                        
        # 240が240になった。出費は240。もうけは0.0
        exp_score0 = 0.0
        for idx in profits.index[1:-3]:
            target_profit = profits.at[idx, 'total_profit']
            print([idx, target_profit])
            check = math.isclose(target_profit, exp_score0, abs_tol = 1e-8)
            self.assertEqual(check, True, f"Row {idx} is not '0.0'")

    def test_calculate_year_first_split_profit(self):

        calculator = InvestmentCalculator(
            sp500_data = self.sp500_data, 
            forex_data = self.forex_data_dict, 
            gogo_split = False, 
            gogo_m5pr = False,
            gogo_year_first = True,
            gogo_year_last_fire = False
        )
        # profits = calculator.calculate_split_investment_profit(sp500_data)
        profits = calculator.calculate_split_investment_profit(self.sp500_data)
                        
        # 240が240になった。出費は240。もうけは0.0
        exp_score0 = 0.0
        for idx in profits.index[1:-3]:
            target_profit = profits.at[idx, 'total_profit']
            print([idx, target_profit])
            check = math.isclose(target_profit, exp_score0, abs_tol = 1e-8)
            self.assertEqual(check, True, f"Row {idx} is not '0.0'")

    def test_calculate_year_last_fire_split_profit(self):

        calculator = InvestmentCalculator(
            sp500_data = self.sp500_data, 
            forex_data = self.forex_data_dict, 
            gogo_split = False, 
            gogo_m5pr = False,
            gogo_year_first = False,
            gogo_year_last_fire = True
        )
        # profits = calculator.calculate_split_investment_profit(sp500_data)
        profits = calculator.calculate_split_investment_profit(self.sp500_data)
                        
        # 240が240になった。出費は240。もうけは0.0
        exp_score0 = 0.0
        for idx in profits.index[1:-3]:
            target_profit = profits.at[idx, 'total_profit']
            print([idx, target_profit])
            check = math.isclose(target_profit, exp_score0, abs_tol = 1e-8)
            self.assertEqual(check, True, f"Row {idx} is not '0.0'")


    def test_calculate_lump_sum_profit(self):

        # 最後の5件を取得・表示
        last_five = list(self.forex_data_dict.items())[-5:]
        for key, value in last_five:
            print(key, value)
        
        for data1 in self.sp500_data[-5:]:
            print(data1)

        calculator = InvestmentCalculator(sp500_data=self.sp500_data, forex_data=self.forex_data_dict)
        profits = calculator.calculate_lump_sum_profit(self.sp500_data)
        print(profits.head(10))
        print([profits.tail(20)])
        
        # 最初は半分
        first_index = profits.index[0]
        forex_ratio = 1.0
        price_ratio = 0.5
        exp_score1 =  (self.nisa_investment * price_ratio * forex_ratio) - self.nisa_investment
        exp_score2 =  ((self.nisa_taxable * price_ratio * forex_ratio ) * (1.0 - 0.2 ) ) - self.nisa_taxable
        exp_score = exp_score1 + exp_score2
        self.assertEqual(profits.at[first_index, 'total_profit'], exp_score, "Last row is not 'minus'")
        
        # 240が240になった。出費は240。もうけは0.0
        # 760が760になった。0.ひひかれて608。出費は760なので-152。
        exp_score0 = ((self.nisa_taxable * 1.0 ) * (1.0 - 0.2 ) ) - self.nisa_taxable
        for idx in profits.index[1:-3]:
            self.assertEqual(profits.at[idx, 'total_profit'], exp_score0, f"Row {idx} is not '0.0'")

        # 最後の行以外をチェック
        last_indices = profits.index[-3:-1]
        # 240が120になって帰ってくる。120もうかった。でも240出費なので-120 
        # 760 * 0.5 = 380で。304もうかった。760かかったので、-476。あわせて
        forex_ratio = 0.5
        exp_score1 =  (self.nisa_investment * forex_ratio) - self.nisa_investment
        exp_score2 =  ((self.nisa_taxable * forex_ratio ) * (1.0 - 0.2 ) ) - self.nisa_taxable
        print([exp_score1, exp_score2, exp_score1 + exp_score2])
        exp_score = exp_score1 + exp_score2
        # 最後の行だけ特別な値かチェック
        for last_index in last_indices:
            self.assertEqual(profits.at[last_index, 'total_profit'], exp_score, "Last row is not 'minus'")

if __name__ == '__main__':
    unittest.main()