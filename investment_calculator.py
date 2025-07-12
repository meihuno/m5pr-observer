from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
import pprint as pp
from itertools import accumulate
import numpy as np

@dataclass
class StockData:
    date: datetime
    price: float
    dayofweek: int

class InvestmentCalculator:
    NISA_INVESTMENT = 2400000  # NISA投資額（240万円）
    NISA_MONTHLY_INVESTMENT = 100000
    NISA_SPLIT_LIMIT = 1200000  # NISA分割投資の上限（120万円）
    NISA_GLOW_LIMIT  = 2400000  # NISA成長投資枠限界（240万円）
    TOTAL_INVESTMENT = 10000000  # 総投資額（1000万円）
    TAXABLE_INVESTMENT = TOTAL_INVESTMENT - NISA_INVESTMENT  # 特定口座投資額
    TAX_RATE = 0.2 # 税率20%
    FOREX_INITIAL_RATE = 115
    
    # M5PR_SLOPE_LIMIT = 20
    M5PR_SLOPE_LIMIT = 10
    M5PR_OUT_RANGE = 300
    
    SP500_PER_THRESHOLD = 30

    def __init__(self, 
                 sp500_data: List[StockData], 
                 forex_data: Dict[datetime, float], 
                 nisa_monthly_date: int = 10, 
                 nisa_monthly_investment: int = 100000,
                 nisa_year_first_investment: int = 2400000,
                 investment_period_year: int = 15,
                 gogo_split = True,
                 gogo_m5pr = False,
                 gogo_year_first = False,
                 gogo_year_last_fire = False,
                 m5pr_skip = False,
                 split_per_boost = False,
                 m5pr_skip_key = 'slope',
                 year_first_control = 'normal', 
                 per_upper = 30, 
                 per_lower = 25,
                 index_name = 'SP500',
                 start_date = '2025-07-01',
                 verbose = True
                 ):
        """
        初期化
        :param forex_data: 為替データ（日付：為替レート）
        """
        self.index_name = index_name
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.forex_data = forex_data
        self.nisa_flag = True
        self.nisa_monthly_date = nisa_monthly_date
        self.total_investment = self.TOTAL_INVESTMENT
        self.monthly_histories = {}
        self.date_str_dict = self._ret_date_str_dict(sp500_data)
        self.nisa_monthly_investment = nisa_monthly_investment
        self.nisa_year_first_investment = nisa_year_first_investment
        self.investment_period_year = investment_period_year
        self.stock_data = sp500_data

        self.gogo_split = gogo_split
        self.gogo_year_first = gogo_year_first
        self.gogo_m5pr = gogo_m5pr
        self.gogo_year_last_fire = gogo_year_last_fire
        self.m5pr_rule = -5.0
        self.m5pr_out_range = InvestmentCalculator.M5PR_OUT_RANGE
        self.m5pr_slope_limit = InvestmentCalculator.M5PR_SLOPE_LIMIT

        self.m5pr_skip_flag = m5pr_skip
        self.m5pr_skip_key = m5pr_skip_key

        self.per_upper = per_upper
        self.per_lower = per_lower

        self.year_first_control = year_first_control

        self.date_price_df = None

        self.split_per_boost = split_per_boost
        
        if gogo_split == True:
            if self.split_per_boost == True:
                split_key = f'split{self.nisa_monthly_investment}-per{per_upper}-boost'
            else:
                split_key = f'split{self.nisa_monthly_investment}'
        else:
            split_key = 'split-skip'

        if m5pr_skip == True:
            # m5pr_skip_key = f"m5pr-slope-skip{self.nisa_monthly_investment}"
            m5pr_skip_key = f"m5pr{self.nisa_monthly_investment}-{m5pr_skip_key}-skip"
        else:
            m5pr_skip_key = "m5pr-gogo"

        if gogo_m5pr == True:
            m5pr_key = f"m5pr{self.nisa_monthly_investment}"
        else:
            m5pr_key = "m5pr-skip"

        if gogo_year_first == True:
            yr_key = f"yearfirst-{year_first_control}"
        else:
            yr_key = "yf-skip"

        if gogo_year_last_fire == True:
            yl_key = "fillinlast"
        else:
            yl_key = "notfillin"

        self.verbose = verbose
        self.filename = f"{self.index_name}_{m5pr_key}_{m5pr_skip_key}_{yr_key}_{yl_key}_{split_key}_investment_results.csv"

        self.sp500_per_dict = self.ret_sp500_per_dict()
        # pp.pprint(self.sp500_per_dict)


    def ret_sp500_per_dict(self):
        df = self.ret_sp500_per_df()
        # 辞書に変換（キーを文字列にする場合）
        result = df.to_dict(orient='records')
        result_dict = {}
        for data in result:
            timestamp1 = data['parsed_date']
            key = timestamp1.strftime('%Y-%m-%d')
            result_dict[key] = data
        # pp.pprint(result_dict)
        return result_dict

    def ret_sp500_per_df(self):
        
        def fix_and_parse_date(s):
            parts = str(s).split(".")
            # print(parts)
            if len(parts) == 2 and parts[1] == 1:
                s = f"{parts[0]}.{parts[1]}0"
            else:
                s = '.'.join(parts)
            return datetime.strptime(s, "%Y.%m")

        # Shiller Excel読み込み（事前にダウンロードしておく）
        df = pd.read_csv("./ie_data.csv")

        df["parsed_date"] = df["Date"].apply(fix_and_parse_date)

        # 年月整形
        df['Date'] = pd.to_datetime(df['parsed_date'], format='%y.%m')
        df.set_index('Date', inplace=True)
        
        # 月次PER計算
        df['PER'] = df['Price'] / df['Earnings']

        return df

    def get_settlement_date_str(self, investment_date: datetime) -> str:
        target_date = self.get_settlement_date(investment_date)
        date_str = target_date.strftime('%Y-%m-%d %H:%M:%S')
        return date_str

    def get_settlement_date(self, investment_date: datetime) -> datetime:
        """約定日の調整をする。約定日を返す。datetimおオブジェクトを返す。
        """
        weekday = investment_date.weekday()  # 月曜:0, 火曜:1, ..., 金曜:4, 土曜:5, 日曜:6

        if weekday in (4, 5, 6):  # 金曜・土曜・日曜()
            # 翌週火曜日
            days_until_tuesday = (1 - weekday) % 7  # 金曜→火曜=+4, 土曜→火曜=+3, 日曜→火曜=+2
            target_date = investment_date + timedelta(days=days_until_tuesday)
        else:
            # 月曜〜木曜：翌営業日（+1日）
            target_date = investment_date + timedelta(days=1)
        return target_date

    def _ret_end_date_data(self, future_date, weekday_data, weekday_data_dict) -> StockData:
        end_data = weekday_data[-1]
        final_data = weekday_data[-1]
        # もし 15年後が今日よりあとの場合は最終日を返す
        # print(["final", final_data])
        if future_date >= final_data.date:
            end_data = final_data
        elif future_date in weekday_data_dict:
            end_data = weekday_data_dict[future_date]
        else:
            # もし、future_dateの日付が存ししていれば、その日付のデータを返す
            # ない場合はある日付まで未来へむかって遡る
            new_date = future_date
            for i in range(0, 100):
                new_date = new_date + timedelta(days=1)
                # print([i, new_date])
                if new_date in weekday_data_dict:
                    end_data = weekday_data_dict[new_date]
                    break
        return end_data

    def _ret_price_date_line_leg(self, sp500_data):
        price_line_dict = {}
        current_date = sp500_data[0].date
        for data in sp500_data:
            date = data.date
            price = int(data.price)
            if not price in price_line_dict:
                price_line_dict[price] = []
            price_line_dict[price].append(date)
        plist = list(price_line_dict.keys())
        pmin = plist[0]
        pmax = plist[-1]
        list1 = price_line_dict[pmin]
        for i in range(pmin, pmax):
            if i in price_line_dict:
                list1 = price_line_dict[i]
            else:
                price_line_dict[i] = list1
        return price_line_dict

    def _ret_date_price_dataframe(self, sp500_data):
        date_list = []
        price_list = []
        for didx, data in enumerate(sp500_data):
            date = data.date
            price = data.price
            date_list.append(date)
            price_list.append(price)
        # データフレーム化
        date_price_df = pd.DataFrame({
            'date': date_list,
            'price': price_list
        })
        return date_price_df

    def _ret_top_price_bewteen_dates(self, start_date, end_date, df):
        # 日付でフィルタ
        # print([type(start_date) ])
        start_date_var = datetime.combine(start_date, datetime.min.time())
        end_date_var = datetime.combine(end_date, datetime.min.time())
        # mask = (df['date'] >= start_date_var) & (df['date'] <= end_date_var)
        
        # print([df.head(10), start_date_var, end_date_var])
        # 条件で絞る
        filtered = df[(df['date'] >= start_date_var) & (df['date'] <= end_date_var)]
        # print(filtered)
        if not filtered.empty:
            max_row = filtered.loc[filtered['price'].idxmax()]
            max_score = max_row['price']
            max_date = max_row['date']
        else:
            max_score = max_date = None

        # print("最大スコア:", max_score)
        # print("その日付:", max_date)

        return max_score, max_date

    def _ret_price_date_line(self, sp500_data):
        price_line_dict = {}
        current_price = int(sp500_data[0].price)
        current_date = sp500_data[0].date
        price_line_dict[current_price] =[current_date]
        for didx, data in enumerate(sp500_data):
            date = data.date
            price = int(data.price)
            if current_price < price:
                idx1 = current_price
                idx2 = price
            else:
                idx1 = price # main
                idx2 = current_price
            for i in range(idx1, idx2+1):
                if not i in price_line_dict:
                    price_line_dict[i] = []
                price_line_dict[i].append(date)
            
            current_price = price
        return price_line_dict

    def _ret_date_str_dict(self, sp500_data):
        weekday_dict = {}
        for data in sp500_data:
            date = data.date
            date_str = date.strftime('%Y-%m-%d %H:%M:%S')
            weekday_dict[date_str] = data
        return weekday_dict

    def _ret_list_sum(self, nums, sidx, eidx):
        cumsum = [0] + list(accumulate(nums))
        # index 1〜3（つまり2〜4）を合計したい → cumsum[4] - cumsum[1]
        total = cumsum[eidx+1] - cumsum[sidx]
        return total

    def _ret_final_output(self, end_data, final_forex, total_buy_point):
        
        print([end_data.date, final_forex])
        # 1口の円換算
        end_price_jpy = end_data.price * final_forex        

        # 買った口数
        final_price_jpy = end_price_jpy * total_buy_point
        
        return final_price_jpy

    def _ret_result_row_dict(self, start_date, end_date, start_price, end_price, price_ratio, forex_ratio, final_buy_point, total_profit):
        result_data = {
            'investment_start_date': start_date,
            'investment_end_date': end_date,
            'start_price': start_price,
            'end_price': end_price,
            'price_ratio': price_ratio,
            'forex_ratio': forex_ratio,
            'final_buy_point': final_buy_point,
            'total_profit': total_profit
        }
        return result_data
    
    def _ret_monthly_indices(self, year, start_year, end_year, start_month, end_month, year_result_dict):
        month_list = year_result_dict[year]['input_money_jpy_split']
        sidx = 0
        eidx = len(month_list) - 1
        start_month_in_a_year = 1
        end_month_in_a_year = 12
        if year == start_year:
            sidx = start_month - 1
            start_month_in_a_year = start_month
        elif year == end_year:
            eidx = end_month - 1
            end_month_in_a_year = end_month
        
        return sidx, eidx, start_month_in_a_year, end_month_in_a_year

    def _ret_each_month_profit(self, total_input_jpy, year, year_result_dict, start_year, end_year, start_month, end_month):
        
        price_jpy_sum = 0.0
        buy_point_sum = 0.0
        price_jpy_glow_sum = 0.0
        buy_point_glow_sum = 0.0

        sidx, eidx, _, _ = self._ret_monthly_indices(year, start_year, end_year, start_month, end_month, year_result_dict)

        # 月毎と投資額を調整する。成長投資は240万で打ち止め
        # 1000万を越えそうなら1000万でストップだ。

        limit_flag = False
        glow_limit = False
        for midx in range(sidx, eidx + 1):
            
            tmp_price_jpy_split = year_result_dict[year]['input_money_jpy_split'][midx]
            tmp_buy_point_split = year_result_dict[year]['buy_point_split'][midx]
            # 
            tmp_price_jpy_glow = year_result_dict[year]['input_money_jpy_glow'][midx]
            tmp_buy_point_glow = year_result_dict[year]['buy_point_glow'][midx]

            if glow_limit == False:
                price_jpy_glow_sum += tmp_price_jpy_glow
                buy_point_glow_sum += tmp_buy_point_glow    
            
            if price_jpy_glow_sum >= self.NISA_GLOW_LIMIT:
                buy_point_glow_sum = tmp_buy_point_glow * (self.NISA_GLOW_LIMIT / price_jpy_glow_sum)
                price_jpy_glow_sum = self.NISA_GLOW_LIMIT
                glow_limit = True

            tmp_price_jpy = tmp_price_jpy_split + tmp_price_jpy_glow
            tmp_buy_point = tmp_buy_point_split + tmp_buy_point_glow

            if total_input_jpy + price_jpy_sum + tmp_price_jpy >= self.TOTAL_INVESTMENT:
                new_tmp_price_jpy = self.TOTAL_INVESTMENT - total_input_jpy - price_jpy_sum
                new_tmp_buy_point = tmp_buy_point * ( new_tmp_price_jpy / tmp_price_jpy )
                tmp_price_jpy = new_tmp_price_jpy
                tmp_buy_point = new_tmp_buy_point
                # print(["limit", total_input_jpy, price_jpy_sum, price_jpy, total_input_jpy + price_jpy_sum + price_jpy])
                limit_flag = True
            
            price_jpy_sum += tmp_price_jpy
            buy_point_sum += tmp_buy_point
            if limit_flag == True:
                break
        
        return price_jpy_sum, buy_point_sum
        

    def _get_fridays_in_month(self, month_start: datetime):
        year = month_start.year
        month = month_start.month

        # 翌月の月初を求める
        if month == 12:
            next_month_start = datetime(year + 1, 1, 1)
        else:
            next_month_start = datetime(year, month + 1, 1)

        current = month_start
        fridays = []

        # 月末まで日を1つずつ進める
        while current < next_month_start:
            if current.weekday() == 4:  # 0=月, ..., 4=金
                fridays.append(current)
            current += timedelta(days=1)

        return fridays

    def _ret_sp500_per_score(self, date1):
        
        if type(date1) is datetime:
            pass
        elif type(date1) is str:
            date1 = datetime.strptime(date1, '%Y-%m-%d')
        
        first_day = date1.replace(day=1) 
        
        # "YYYY-MM-DD" 形式に変換
        date_str = first_day.strftime('%Y-%m-%d')
        sp500_per = 30
        if date_str in self.sp500_per_dict:
            sp500_per = self.sp500_per_dict[date_str]['PER']
        return sp500_per
        

    def _check_m5pr_ageage_expectation(self, price, date):
        
        def nearest_day(target_date, dates):
            np_dates = np.array(dates, dtype='datetime64[D]')

            # 基準日 A
            threshold = np.datetime64(target_date - timedelta(days=7))

            # 7日前以前の要素をフィルタ
            filtered = np_dates[np_dates < threshold]

            # 最も新しい日付（なければ None）
            result = filtered.max() if filtered.size > 0 else None
            if not result is None:
                # numpの日付なので普通のdatetimeに変換して返す。
                # numpののdatetimeはこの関数な中だけにとどまる。
                py_datetime = result.astype(datetime)
                return py_datetime
            return result

        def ret_slope(date1, score1, date2, score2):
            days_diff = (date2.date() - date1).days

            # print([days_diff, date1, date2, score1, score2])
            # ゼロ除算防止
            if days_diff != 0:
                slope = (score2 - score1) / days_diff
            else:
                slope = None  # or float('inf') if you prefer
            
            # print("傾き:", slope)
            return slope


        rflag = True
        if price in self.price_date_line_dict:
            list1 = self.price_date_line_dict[price]
            index1 = list1.index(date)
            if not index1 == 0:
                
                date1 = nearest_day(date, list1)
                first_day = date1.replace(day=1)
                # "YYYY-MM-DD" 形式に変換
                date_str = first_day.strftime('%Y-%m-%d')
                
                sp500_per = 1
                if date_str in self.sp500_per_dict:
                    sp500_per = self.sp500_per_dict[date_str]['PER']
                    # print(["PER", date1, price, sp500_per])
                max_score, max_date = self._ret_top_price_bewteen_dates(date1, date, self.date_price_df)
                slope = ret_slope(date1, price, max_date, max_score)
                if not date1 is None:
                    delta = date.date() - date1
                    if self.m5pr_skip_flag == True:
                        if self.m5pr_skip_key == 'slopeday' and ( slope > self.m5pr_slope_limit or delta.days < self.m5pr_out_range): 
                            rflag = False
                        elif self.m5pr_skip_key == 'slope' and slope > self.m5pr_slope_limit:
                            rflag = False
                        elif self.m5pr_skip_key == 'day' and delta.days < self.m5pr_out_range:
                            rflag = False
                        elif self.m5pr_skip_key == 'per' and sp500_per > self.per_upper:
                            rflag = False
                        if rflag == True:
                            print(["safe line", delta, price, date1, '->', date, "slope", slope])
                        elif rflag == False:
                            print(["danger line", delta, price, date1, '->', date, "slope", slope])
                    else:
                        print(["gogo m5pr", delta, price, date1, '->', date, "slope", slope])
                        
        return rflag
    
    def _ret_m5pr_result(self, fridays, date_str_dict):
        m5pr_result = 0.0
        for friday in fridays:
            pfriday = friday - timedelta(weeks=1)
            pfriday_str = pfriday.strftime('%Y-%m-%d %H:%M:%S')
            friday_str = friday.strftime('%Y-%m-%d %H:%M:%S')
            if pfriday_str in date_str_dict and friday_str in date_str_dict:
                pprice = date_str_dict[pfriday_str].price
                price = date_str_dict[friday_str].price
                change_percent = (price - pprice) / pprice * 100
                # print([pfriday_str, pprice, friday_str, price])
                if change_percent < self.m5pr_rule:
                    if self._check_m5pr_ageage_expectation(int(price), friday) == True:
                        m5pr_result += 1
                        print(["Down!", friday_str, pprice, "->", price, change_percent])
                    else:
                        print(["Skip!", friday_str, pprice, "->", price, change_percent])            

        return m5pr_result
    
    def _ret_year_glow_sum(self, month_glow_list, buy_point_glow_list):
        # 成長の上限は年初からの買い付けた足し合わせて調整するか為替え影響あありそうなので        
        tmp_jpy_glow_sum = 0.0
        tmp_buy_point_glow_sum = 0.0
        for mgidx, tmp_price_jpy_glow in enumerate(month_glow_list):
            tmp_buy_point_glow = buy_point_glow_list[mgidx]
            tmp_buy_point_glow_sum += tmp_buy_point_glow
            tmp_jpy_glow_sum += tmp_price_jpy_glow
            if tmp_jpy_glow_sum == self.NISA_GLOW_LIMIT:
                price_jpy_glow_sum = self.NISA_GLOW_LIMIT
                buy_point_glow_sum = tmp_buy_point_glow
                break
            elif tmp_jpy_glow_sum > self.NISA_GLOW_LIMIT:
                price_jpy_glow_sum = self.NISA_GLOW_LIMIT
                buy_point_glow_sum = tmp_buy_point_glow * (self.NISA_GLOW_LIMIT / tmp_jpy_glow_sum)
                break
        return price_jpy_glow_sum, buy_point_glow_sum

    def _ret_accumulate_profit(self, year, year_result_dict, start_year, end_year, start_month, end_month):
        """年毎の積み立て額をまとめて取得する。
        """

        month_split_list = year_result_dict[year]['input_money_jpy_split']
        buy_point_split_list = year_result_dict[year]['buy_point_split']

        month_glow_list = year_result_dict[year]['input_money_jpy_glow']
        buy_point_glow_list = year_result_dict[year]['buy_point_glow']

        sidx, eidx, start_month_in_a_year, end_month_in_a_year = self._ret_monthly_indices(year, start_year, end_year, start_month, end_month, year_result_dict)

        month_key = f"{year}-{start_month_in_a_year:02d}-{end_month_in_a_year:02d}"
        # print([year, sidx, eidx, start_month, end_month, month_key])
        if month_key in self.monthly_histories:
            price_jpy_split_sum = self.monthly_histories[month_key]['price_jpy_split_sum']
            buy_point_split_sum = self.monthly_histories[month_key]['buy_point_split_sum']
            price_jpy_glow_sum = self.monthly_histories[month_key]['price_jpy_glow_sum']
            buy_point_glow_sum = self.monthly_histories[month_key]['buy_point_glow_sum']
        else:
            # 年単位ままとめけ計算
            price_jpy_split_sum = self._ret_list_sum(month_split_list, sidx, eidx)
            buy_point_split_sum = self._ret_list_sum(buy_point_split_list, sidx, eidx)

            price_jpy_glow_sum = self._ret_list_sum(month_glow_list, sidx, eidx)
            buy_point_glow_sum = self._ret_list_sum(buy_point_glow_list, sidx, eidx)

            # 成長の上限は年初からの買い付けた足し合わせて調整するか為替え影響あありそうなので
            if price_jpy_glow_sum > self.NISA_GLOW_LIMIT:
                price_jpy_glow_sum, buy_point_glow_sum = self._ret_year_glow_sum(month_glow_list, buy_point_glow_list)

            self.monthly_histories[month_key] = {
                'price_jpy_split_sum': price_jpy_split_sum,
                'buy_point_split_sum': buy_point_split_sum,
                'price_jpy_glow_sum': price_jpy_glow_sum,
                'buy_point_glow_sum': buy_point_glow_sum
                }
        
        price_jpy_sum = price_jpy_split_sum + price_jpy_glow_sum
        buy_point_sum = buy_point_split_sum + buy_point_glow_sum
        return price_jpy_sum, buy_point_sum

    def calculate_split_investment_profit(self, sp500_data: List[StockData]) -> Dict[datetime, float]:
        """
        分と投資の利益け計算する。
        :param sp500_data: SP500の価格データリスト
        :return: 各日付の利益
        """

        def get_monthly_dates(start_date, end_date, date_str_dict, day=10):
            
            current = start_date.replace(month=1, day=day)
            end_current = end_date.replace(month=12)

            start_month = start_date.month
            if start_date.day >= self.nisa_monthly_date:
                tmp_start_date = start_date + relativedelta(months=1)
                start_month = tmp_start_date.month

            year_dict = {}
            year_count = 0
            # 存在しない月も値を持つ必要がある。適当なintの値をいれておく
            initial_forex = self.FOREX_INITIAL_RATE
            while current <= end_current:
                
                year = current.year
                if not year in year_dict:
                    year_dict[year] = { 
                        'date_str':[], 
                        'settlement_date_str':[], 
                        'price':[], 
                        'forex':[], 
                        'input_money_jpy':[], 
                        'input_money_jpy_split':[],
                        'input_money_jpy_glow':[],
                        'buy_point':[],
                        'buy_point_split':[],
                        'buy_point_glow':[],
                        'm5pr_down_count':[] 
                    }
                    year_count += 1
                
                settlement_date = self.get_settlement_date(current)
                settlement_date_str = settlement_date.strftime('%Y-%m-%d %H:%M:%S')
                trial_count = 0
                if not settlement_date_str in date_str_dict:
                    while settlement_date_str not in date_str_dict:
                        settlement_date += timedelta(days=1)
                        settlement_date_str = settlement_date.strftime('%Y-%m-%d %H:%M:%S')
                        trial_count += 1
                        if trial_count > 10:
                            # print(["settlement_date", settlement_date_str, "not found"])
                            break

                date_str = current.strftime('%Y-%m-%d %H:%M:%S')

                if settlement_date_str in date_str_dict:
                    data = date_str_dict[settlement_date_str]
                    month_first_day = current.replace(day=1)
                    # month_first_day = settlement_date.replace(day=1)

                    fridays = self._get_fridays_in_month(month_first_day)
                    m5pr_down_count = self._ret_m5pr_result(fridays, date_str_dict)
                    
                    sp500_per = self._ret_sp500_per_score(month_first_day)
                
                    input_jpy_split = 0.0
                    if self.gogo_split == True:
                        input_jpy_split = self.nisa_monthly_investment

                    if self.gogo_m5pr == True:
                        m5pr_price = 12 * self.nisa_monthly_investment * m5pr_down_count
                    else:
                        m5pr_price = 0.0

                    # current
                    if self.split_per_boost == True:
                        if sp500_per < self.per_lower:
                            m5pr_price += self.nisa_monthly_investment
                    
                    if self.gogo_year_first == True:
                        if current.month == 1:
                            m5pr_price += self.nisa_year_first_investment
                        elif self.year_first_control == 'first_attack' and  year_count == 1 and start_month == current.month:
                            m5pr_price += self.nisa_year_first_investment

                    # 年末に年間投資枠がうまってなかったらつめておく
                    if self.gogo_year_last_fire == True:
                        if current.month == 12:
                            m5pr_price = self.NISA_GLOW_LIMIT

                    # 一括投資ば場合ここに計がが入る
                    if settlement_date_str in self.forex_data:  
                        initial_forex = self.forex_data[settlement_date_str]['rate']            

                    # 10万円をドルに変える
                    input_target_currency = input_jpy_split / initial_forex
                    input_target_currency_split = input_jpy_split / initial_forex
                    input_target_currency_glow = m5pr_price / initial_forex
                    # SP500をいくか買えるか
                    """ Todo """
                    # （メモ）priceまマイナス5%ルールおよび年初一括投資の投資日でそれぞけ計算すること
                    buy_point = input_target_currency / data.price
                    buy_point_split = input_target_currency_split / data.price
                    buy_point_glow = input_target_currency_glow / data.price

                    year_dict[year]['date_str'].append(date_str)
                    year_dict[year]['settlement_date_str'].append(settlement_date_str)
                    year_dict[year]['price'].append(data.price)
                    year_dict[year]['forex'].append(initial_forex)
                    year_dict[year]['input_money_jpy'].append(0.0)
                    year_dict[year]['input_money_jpy_split'].append(input_jpy_split)
                    year_dict[year]['input_money_jpy_glow'].append(m5pr_price)
                    year_dict[year]['buy_point'].append(buy_point)
                    year_dict[year]['buy_point_split'].append(buy_point_split)
                    year_dict[year]['buy_point_glow'].append(buy_point_glow)
                    year_dict[year]['m5pr_down_count'].append(m5pr_down_count)
                else:
                    year_dict[year]['date_str'].append(date_str)
                    year_dict[year]['settlement_date_str'].append(settlement_date_str)
                    year_dict[year]['price'].append(0.0)
                    year_dict[year]['forex'].append(initial_forex)
                    year_dict[year]['input_money_jpy'].append(0.0)
                    year_dict[year]['input_money_jpy_split'].append(0.0)
                    year_dict[year]['input_money_jpy_glow'].append(0.)
                    year_dict[year]['buy_point'].append(0.0)
                    year_dict[year]['buy_point_glow'].append(0.0)
                    year_dict[year]['buy_point_split'].append(0.0)
                    year_dict[year]['m5pr_down_count'].append(0.0)
                    
                    print(["lost one", date_str, settlement_date_str])

                current += relativedelta(months=1)
                
            return year_dict

        def ret_split_investment_profit(start_data, end_data, year_result_dict):
            
            start_date = start_data.date
            end_date = end_data.date
            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

            current = start_date.replace(day=self.nisa_monthly_date)
            end_current = end_date.replace(day=self.nisa_monthly_date)
            
            end_month = end_date.month
            # 10日以降なつ翌月スタート
            if start_date.day >= self.nisa_monthly_date:
                current = current + relativedelta(months=1)
            
            if end_date.day < self.nisa_monthly_date:
                end_current = end_current - relativedelta(months=1)
                
            total_input_jpy = 0.0
            total_buy_point = 0.0

            start_year = current.year
            end_year = end_current.year
            start_month = current.month
            end_month = end_current.month
            finish_year_count = 0

            for year in range(start_year, end_current.year + 1):
                if year in year_result_dict:
                    # この1でTOTAL_INVESTMENTを超えてしまう可能性がある場合は、月毎に計算に切り替える。
                    # 240+120を超える可能ががあるんだ
                    if total_input_jpy + self.NISA_SPLIT_LIMIT + self.NISA_GLOW_LIMIT >= self.TOTAL_INVESTMENT:
                        price_jpy_sum, buy_point_sum = self._ret_each_month_profit(total_input_jpy, year, year_result_dict, start_year, end_year, start_month, end_month)
                    else:
                        price_jpy_sum, buy_point_sum = self._ret_accumulate_profit(year, year_result_dict, start_year, end_year, start_month, end_month)
                    
                    total_buy_point += buy_point_sum
                    total_input_jpy += price_jpy_sum
                    if self.verbose == True:
                        print([year, start_date_str, end_date_str, buy_point_sum, price_jpy_sum, total_buy_point, total_input_jpy])
                    
                    finish_year_count += 1
                    if total_input_jpy >=  self.TOTAL_INVESTMENT:
                        break

            initial_forex = None
            final_forex = None
            end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            if end_date_str in self.forex_data:
                final_forex = self.forex_data[end_date_str]['rate']
            
            # 現在の約定日の為替レートを取得
            start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if start_date_str in self.forex_data:  
                initial_forex = self.forex_data[start_date_str]['rate']

            final_output_jpy = self._ret_final_output(end_data, final_forex, total_buy_point)
            total_profit = final_output_jpy - total_input_jpy
            # print([start_date, end_date, start_data.price, '->', end_data.price,  total_input_jpy, '->', final_output_jpy, initial_forex, '->', final_forex, total_buy_point])
            price_ratio = end_data.price / start_data.price 
            forex_ratio = final_forex / initial_forex
            
            if self.verbose == True:
                print(["final", start_date_str, end_date_str, start_data.price, "end", end_data.price, price_ratio, final_output_jpy, total_input_jpy, total_profit, total_buy_point, finish_year_count])

            # res = self._ret_result_row_dict(start_date, end_date, current_data.price, end_data.price, price_ratio, forex_ratio, total_buy_point, total_profit)
            res = self._ret_result_row_dict(start_date, end_date, start_data.price, end_data.price, price_ratio, forex_ratio, total_buy_point, total_profit)
            return res
        # friday_data = [data for data in sp500_data if data.dayofweek == 4 and data.date > datetime(1996, 10, 30)]
        """
        target_data = [data for data in sp500_data if data.dayofweek < 5 and data.date > datetime(1996, 10, 30)]
        weekday_dict = {}
        for data in target_data:
            weekday_dict[data.date] = data
        """

        target_data, weekday_dict = self.ret_target_data(sp500_data)
        start_date = target_data[0].date
        end_date = target_data[-1].date
        date_str_dict = self._ret_date_str_dict(sp500_data)
        self.date_price_df = self._ret_date_price_dataframe(sp500_data)
        
        self.price_date_line_dict = self._ret_price_date_line(sp500_data)
        
        year_result_dict = get_monthly_dates(start_date, end_date, date_str_dict, day=10)
        
        # datafsrameにする。月のドル円
        # 開始日時から終了日ままでの、年毎に、月ごとの積み立て額を取得する。その時の為替額で値をつくる。
        # 年毎の一括投資LINEと積み立て投資ラインを

        for i, current_data in enumerate(target_data):
            
            #　投資期間が15年未満の場合はスキップ
            #  stock_dataはdummyで未来のデータ。
            if current_data.date >= datetime.today():
                pass
            else:
                if current_data.date > datetime.today() - relativedelta(years=self.investment_period_year):
                    continue

            # 投資開始日から15年後のデータを取得
            investment_date = current_data.date
            future_date = investment_date + relativedelta(years=self.investment_period_year)
            future_end_data = self._ret_end_date_data(future_date, target_data, weekday_dict)
            
            result_data = ret_split_investment_profit(current_data, future_end_data, year_result_dict)

            # もし初回の処理であれば、DataFrameを新規作成
            if not hasattr(self, 'results_df'):
                self.results_df = pd.DataFrame(columns=result_data.keys())
                
            # 結果を追加
            self.results_df = pd.concat([self.results_df, pd.DataFrame([result_data])], ignore_index=True)

        return self.results_df

    def _ret_buy_point(self, input, score, ratio):
        """
        input 100万円、
        score 5000、
        1ドル100だった場合、
        buy_point は 100万/100= 1万ドル、1万ドルなんで10000/5000で2口というふうに計すする
        """
        buy_point = (input/ratio) / score
        return buy_point

    def _ret_final_price_jpy(self, input, price1, initial_forex, price2, final_forex):
        """投資時の買った口数。
        その口数ぶんだけoutputの値段のドルが得られる。
        ドルを日本円に戻して、最後に日本円が得られる
        """
        buy_point = self._ret_buy_point(input, price1, initial_forex)
        final_price = buy_point * price2
        final_price_jpy = final_price * final_forex 
        return final_price_jpy
        

    def calculate_lump_sum_profit(self,  sp500_data: List[StockData]) -> Dict[datetime, float]:
        """
        一括投資
        投資利益を計算
        :param sp500_data: SP500の価格データリスト
        :return: 各日付の利益
        """
        
        target_data, weekday_dict = self.ret_target_data(sp500_data)

        for i, current_data in enumerate(target_data):
            
            initial_forex = None
            final_forex = None
            
            #　投資期間が15年未満の場合はスキップ
            #  stock_dataはdummyで未来のデータ。
            if current_data.date >= datetime.today():
                pass
            else:
                if current_data.date > datetime.today() - relativedelta(years=self.investment_period_year):
                    continue
            
            # 投資開始日から15年後のデータを取得
            investment_date = current_data.date
            future_date = investment_date + relativedelta(years=self.investment_period_year)
            
            # 現在の約定日の為替レートを取得
            settlement_date = self.get_settlement_date_str(investment_date)
            
            if settlement_date in self.forex_data:  
                initial_forex = self.forex_data[settlement_date]['rate']

            # print(["一括Gogo", "開始", investment_date, "翌の火曜", settlement_date, initial_forex])
            if not initial_forex:
                continue

            # 15年後のデータを探す
            end_data = self._ret_end_date_data(future_date, target_data, weekday_dict)
            
            if end_data:
                # 最終日の為替レートを取得
                final_settlement_date = self.get_settlement_date_str(end_data.date)
                
                if final_settlement_date in self.forex_data:
                    final_forex = self.forex_data[final_settlement_date]['rate']
                # print([end_data.date, final_settlement_date, final_forex])
                if not final_forex:
                    continue
                    # 結果をリストに格納してDataFrameを作成するためのデータを準備
                
                """
                end_price_jpy = end_data.price * final_forex        

                # 買った口数
                final_price_jpy = end_price_jpy * total_buy_point
            
                # 価格変化率
                price_ratio = final_price_jpy / input_money_jpy
                                
                """
                # 価格
                nisa_input = self.NISA_INVESTMENT
                nisa_buy_point = self._ret_buy_point(nisa_input, current_data.price, initial_forex)
                nisa_output = self._ret_final_price_jpy(nisa_input, current_data.price, initial_forex, end_data.price, final_forex)
                nisa_profit = nisa_output - nisa_input

                tokutei_input = self.TAXABLE_INVESTMENT
                tokutei_buy_point = self._ret_buy_point(tokutei_input, current_data.price, initial_forex)
                tokutei_output = self._ret_final_price_jpy(tokutei_input, current_data.price, initial_forex, end_data.price, final_forex)
                taxed_profit = ( (tokutei_output) * (1 - self.TAX_RATE) ) - tokutei_input
                
                # 総利益
                final_buy_point = nisa_buy_point + tokutei_buy_point
                price_ratio = end_data.price/current_data.price
                forex_ratio = final_forex / initial_forex
                total_profit = nisa_profit + taxed_profit
                
                result_data = self._ret_result_row_dict(investment_date, end_data.date, current_data.price, end_data.price, price_ratio, forex_ratio, final_buy_point, total_profit)
                
                # もし初回の処理であれば、DataFrameを新規作成
                if not hasattr(self, 'results_df'):
                    self.results_df = pd.DataFrame(columns=result_data.keys())
                
                # 結果を追加
                self.results_df = pd.concat([self.results_df, pd.DataFrame([result_data])], ignore_index=True)
                
        return self.results_df
        

    def ret_target_data(self, sp500_data: List[StockData]) -> Dict[datetime, float]:

        target_data = [data for data in sp500_data if data.dayofweek < 5 and data.date > self.start_date]
        # target_data = [data for data in sp500_data if data.dayofweek < 5 and data.date > datetime(1996, 10, 30)]
        weekday_dict = {}
        for data in target_data:
            weekday_dict[data.date] = data
        
        return target_data, weekday_dict

