from datetime import datetime, timedelta
from download_stock_info import DatabaseManager
from download_stock_info import IndexFetcher
from wordpress_page_content import WordPressPageContent
from daytime_util import DayTimeUtil
from database_manager import WordpressDatabaseManager
import holidays

import pprint as pp

WEEK_NUM_FRIDAY = 4
MINUS_5PERCENT_RULE = -5.0

class WordPressPageContentMaker(object):
    """Wordpressに表示する内容を生成する。なるべくタグは含めないようにする。なるべく。"""

    def __init__(self, phase='deploy', datestr=None):

        self.phase = phase
        self.today = datetime.now()
        if phase == 'test':
            if not datestr is None:
                date_format = "%Y-%m-%d"
                self.today = datetime.strptime(datestr, date_format)
    
    
    def _ret_db_manager(self):
        """テスト時にはテスト用のdbを読み込む。"""
        if self.phase == 'test':
            db_manager = DatabaseManager(db_name='index_test.sqlite')
        else:
            db_manager = DatabaseManager()
        return db_manager


    def ret_latest_value_of_week(self, key, date_str):
        db_manager = self._ret_db_manager()
        value_this_week = db_manager.get_latest_value_of_week(key, date_str)
        db_manager.close()
        return value_this_week

    ### 外だ出したい。今はサボる
    def _updown_string(self, percentage_change):
        updown = str(round(percentage_change, 3))
        if percentage_change < 0.0:
            # updown = '&#8595;' + updown
            updown = '(Down)' + updown + "%"
        else:
            # updown = '&#8593;' + updown
            updown = '(Up)+' + updown + "%"
        return updown
    
    def _ret_rule_status(self, percentage_change):
        result_state = '発動せず'
        # スコアについては検討する
        if percentage_change < (MINUS_5PERCENT_RULE * 3.0) :
            result_state = '発動中（未曾有の大暴落）!!'
        elif percentage_change < (MINUS_5PERCENT_RULE * 2.0):
            result_state = '発動中（暴落）!!'
        elif percentage_change < MINUS_5PERCENT_RULE:
            result_state = '発動中！'
        elif percentage_change > 5.0:
            result_state = '発動せず（急騰中）'
        
        return result_state

    def _ret_date_str(self, today):
        today_str = today.strftime('%Y-%m-%d 00:00:00')
        return today_str

    def _ret_previous_friday(self, today):
        # 前の金曜日を返す
        weekday = today.weekday()
        offset = (today.weekday() - 4) % 7
        if weekday == WEEK_NUM_FRIDAY:
            previous_friday = today - timedelta(days=offset + 7)
        else:
            previous_friday = today - timedelta(days=offset)
        return previous_friday

    def _ret_last_friday(self, today):
        # 週末用の関数であり、先週(1つ前の週の)の金曜日を返す。
        offset = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=offset + 7)
        return last_friday

    def _get_monday_of_week(self, date):
        monday = date - timedelta(days=date.weekday())
        monday_str = monday.strftime('%Y-%m-%d 00:00:00')
        return monday_str

    def _ret_threshold(self, value):
        return str(round(value * 0.95, 3))

    def check_friday_index_value(self, today, index_key_list):

        # 米国の株式市場の休日（連邦祝日をベースに）
        us_holidays = holidays.US()

        def is_us_market_holiday(date):
            # date は datetime.date 型
            # 祝日かつ土日でない場合のみ市場休みとみなす
            return date in us_holidays and date.weekday() < 5

        db_manager = self._ret_db_manager()
        last_friday = self._ret_previous_friday(today)
        last_friday_str = self._ret_date_str(last_friday)
        
        gogo_weekend_flag = True
        for key in index_key_list:
            value = db_manager.get_value_by_date(key, last_friday_str)
            
            # 金曜日で値取得できていないindexがある場合は週末判定はFalse
            if value is None:
                # 米国が市場休みの場合は値が取得できていない（value=None）場合でもFalsににはならない
                if not is_us_market_holiday(last_friday):
                    gogo_weekend_flag = False
        db_manager.close()
        return gogo_weekend_flag

    def ret_weekday_page_content(self, today, index_key_list):
        status_line_dict = self.ret_weekday_status_dict(today, index_key_list)
        wppc_box = WordPressPageContent()
        rline = wppc_box.ret_weekday_content(today, status_line_dict)

        #休日にもしも5%ルール発動していたら、スライドショー_をONなのである。
        if self._is_week_day_rule_ignited(status_line_dict) == True:
            print("Hide False = Slide On")
            self.switch_slide_show_hide(False) 
        else:
            print("Hide True = Slide Off")
            self.switch_slide_show_hide(True) 
        return rline

    def ret_weekday_status_dict(self, today, index_key_list):
        # 平日のコンテンツはそもそも週末とは異なる。
        # 今日は2024年07月29日です。5%ルールは発動していません。
        # SP500のテーブル。
        # NASDAQ100のテーブル。

        def ret_weekday_row_dict(dateday, value, updown, p1, th, weekday):
            tmp_dict = {}
            tmp_dict['day'] = dateday
            tmp_dict['weekday'] = weekday
            tmp_dict['value'] = str(round(value, 3))
            tmp_dict['updown'] = updown
            tmp_dict['status'] = self._ret_rule_status(p1)
            tmp_dict['threshold'] = th
            tmp_dict['percentage_change'] = p1

            return tmp_dict

        yesterday = today - timedelta(days=1)
        today_str = self._ret_date_str(today)
        yesterday_str = self._ret_date_str(yesterday)

        status_dict = {}
        dateutil_obj = DayTimeUtil()
        for key in index_key_list:
            # indexをセット
            if not key in status_dict:
                status_dict[key] = []
            
            last_friday = self._ret_previous_friday(today)
            last_friday_str = self._ret_date_str(last_friday)
            
            one_week_ago_friday = last_friday - timedelta(days=7)
            one_week_ago_friday_str = one_week_ago_friday.strftime('%Y-%m-%d 00:00:00')
            
            # 先週の金曜日の結果をくれ
            last_friday_value, last_last_friday_value ,p1, updown = self._ret_value_updown_series(key, last_friday_str, one_week_ago_friday_str)
            threshold = self._ret_threshold(last_last_friday_value)
            print([last_friday, one_week_ago_friday_str, last_friday_value, last_last_friday_value, p1, updown])
            # datetimeオブジェクトに変換
            # date_object = datetime.strptime(date_s, '%Y-%m-%d %H:%M:%S')
            
            last_friday_dateday = dateutil_obj.ret_dateday_string('先週', last_friday)
            last_friday_weekday = -1
            tmp_dict = ret_weekday_row_dict(last_friday_dateday, last_friday_value, updown, p1, threshold, last_friday_weekday)
            status_dict[key].append( tmp_dict )

            # 今週の月曜日の日付            
            this_monday_str = self._get_monday_of_week(today)
            # 今週の週頭からの結果を取得
            db_manager = self._ret_db_manager()
            rowsa = db_manager.get_week_rows(key, this_monday_str, today_str)
            rowsb = db_manager.get_week_rows(key, this_monday_str, yesterday_str)
            rows = []
            if len(rowsa) > 0:
                rows = rowsa
            elif len(rowsb) > 0:
                rows = rowsb

            for row in rows:
                row_value = row[2]
                row_date_string =  row[3]
                date_object = datetime.strptime(row_date_string, '%Y-%m-%d %H:%M:%S')
                this_week_dateday = dateutil_obj.ret_dateday_string('今週', date_object)

                tmp_percentage_change = self._ret_percentage_change(row_value, last_friday_value)
                tmp_threshold = self._ret_threshold(last_friday_value)
                tmp_weekday = date_object.weekday()
                tmp_updown = self._updown_string(tmp_percentage_change)
                tmp_dict = ret_weekday_row_dict(this_week_dateday, row_value, tmp_updown, tmp_percentage_change, tmp_threshold, tmp_weekday)
                status_dict[key].append( tmp_dict )
        
        return status_dict
        # その日の結果をくれ

    def _ret_percentage_change(self, value_this_week, value_last_week):
        percentage_change = ((value_this_week - value_last_week) / value_last_week) * 100
        return percentage_change
    
    def _ret_value_updown_series(self, key, date_str, one_week_ago_today_str):

        value_this_week = self.ret_latest_value_of_week(key, date_str)
        value_last_week = self.ret_latest_value_of_week(key, one_week_ago_today_str)
        
        # 今週の先週の値をゲット
        percentage_change = self._ret_percentage_change(value_this_week, value_last_week)
        updown = self._updown_string(percentage_change)

        return value_this_week, value_last_week, percentage_change, updown

    def ret_weekend_status_dict(self, today, index_key_list):
        
        today_str = self._ret_date_str(today)
        one_week_ago_today = today - timedelta(7)
        one_week_ago_today_str = one_week_ago_today.strftime('%Y-%m-%d 00:00:00')

        status_dict = {}
        for key in index_key_list:
            # indexごとのRowに当たるデータを辞書に詰めていく
            # indexをセット
            if not key in status_dict:
                status_dict[key] = {}
            
            # FIXME. DBとの通信とテーブルの生成は別メソッドにしたほうがテストしやすかった。
            value_this_week = self.ret_latest_value_of_week(key, today_str)
            value_last_week = self.ret_latest_value_of_week(key, one_week_ago_today_str)
            
            # 今週の先週の値をゲット
            percentage_change = self._ret_percentage_change(value_this_week, value_last_week)
            updown = self._updown_string(percentage_change)
            result_state = self._ret_rule_status(percentage_change)
            # WordpressのHTMLもこのクラスでやった方がいい。キーが異なるクラスに渡るのはよくない

            status_dict[key]['updown'] = updown
            status_dict[key]['status'] = result_state
            status_dict[key]['past_value'] = str(round(value_last_week, 3))
            status_dict[key]['value'] = str(round(value_this_week, 3))
            status_dict[key]['percentage_change'] = percentage_change
            
            # 上昇、下降を判定。上昇なら黒色、下降なら赤色、
            print([key, value_last_week, value_this_week, percentage_change])
        
        return status_dict

    def ret_weekend_page_content(self, today, index_key_list):
        status_dict = self.ret_weekend_status_dict(today, index_key_list)
        print(status_dict)
        wppc_box = WordPressPageContent()
        content_line = wppc_box.ret_weekend_content(today, status_dict)
        
        #休日にもしも5%ルール発動していたら、スライドショー_をONなのである。
        if self._is_rule_ignited(status_dict) == True:
            self.switch_slide_show_hide(False) 
        else:
            self.switch_slide_show_hide(True) 
        
        return content_line

    def switch_slide_show_hide(self, flag=False):
        db_manager = WordpressDatabaseManager(
            host="127.0.0.1",
            user="root",
            password="root",
            database="local",
            port=10004
        )
        try:
            res = db_manager.get_value(
                table="wp_options",
                column="option_value",
                # value="option_value",
                condition="option_name='lightning_theme_options'"
            )
            res['top_slide_hide'] = flag

            new_serialized_data = db_manager._php_decode(res)
            print(["set", new_serialized_data])
            db_manager.set_value(
                table="wp_options",
                column="option_value",
                value= new_serialized_data,
                condition="option_name='lightning_theme_options'"
            )
            
        finally:
            db_manager.close()

    def _is_week_day_rule_ignited(self, status_line_dict):
        # 水曜以降に-2.5%以下の下落だっ場場合、可能性
        # 水曜日以に-5.0%以下の下落だっば場合、がちっぽい
        for _, status_dict_lines in status_line_dict.items():
            for sub_dict1 in status_dict_lines:
                # 水曜日から金ままででスコアに応じてフラか返す
                if sub_dict1['weekday'] > 1 and sub_dict1['weekday'] < 5:
                    if sub_dict1['percentage_change'] < MINUS_5PERCENT_RULE:
                        return True
        return False

    def _is_rule_ignited(self, status_dict):
        for key, sub_dict1 in status_dict.items():
            if sub_dict1['percentage_change'] < MINUS_5PERCENT_RULE:
                return True
        return False

    def ret_content_of_today(self):
        """その日のWordPress記事のコンテンツを返す
        | 週末か平日かでWordPressのページの内容を変える。
        | Sqliteのデータベースを検索する。
        | WordPressのページを編集するオブジェクトの入力となる。

        Returns: その日のコンテンツのHTML
        """
        # 週末か平日かでWordPressのページの内容を変える
        rcontent = 'Something wrong!'
        
        fetcher = IndexFetcher()
        index_key_list = fetcher.ret_index_symbol_list()

        today = self.today
        dayofweek = today.weekday()

        check_friday_index_value = self.check_friday_index_value(today, index_key_list)
        
        # 平日か週末かで分岐
        if dayofweek > WEEK_NUM_FRIDAY and check_friday_index_value == True:
            # 週末だ！
            print("Week End!")
            rcontent = self.ret_weekend_page_content(today, index_key_list)
            print(rcontent)

        elif dayofweek >= 0: #and dayofweek <= WEEK_NUM_FRIDAY:
            # 平日だ！
            print("Week Day!")
            rcontent = self.ret_weekday_page_content(today, index_key_list)
            # print(rcontent)
        
        return rcontent
        
