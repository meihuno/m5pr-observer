import sqlite3
from datetime import datetime, timedelta
import json
import yfinance as yf
from dateutil import parser
import pprint as pp
import option_util as ou
from edit_wordpress import EditWordPress
from wordpress_page_content import WordPressPageContent
import pandas as pd

class IndexData:
    def __init__(self, symbol, value, date, download_date, dayofweek):
        self.symbol = symbol
        self.value = value
        self.date = date
        self.download_date = download_date
        self.dayofweek = dayofweek

class IndexFetcher:
    def __init__(self):
        self.symbols = {
            'SP500': '^GSPC',
            'NASDAQ100': '^NDX',
            'NIKKEI225': '^N225'
            # 'NASDAQ': '^IXIC',
        }
        self.stockchats_urls = {
            'SP500' :    'https://stockcharts.com/sc3/ui/?s=%24SPX',
            'NASDAQ100': 'https://stockcharts.com/sc3/ui/?s=%24NDX', 
            'NIKKEI225': 'https://stockcharts.com/sc3/ui/?s=%24N225', 
        }


    def fetch(self, period='1d'):
        index_data_list = []
        for name, symbol in self.symbols.items():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)

            for row in data.itertuples():
                # print(f"インデックス: {row.Index}, 行データ: {row.Close}")
                date_str = row.Index.strftime('%Y-%m-%d %H:%M:%S')
                value = row.Close
                date_obj = parser.parse(date_str)
                dayofweek = date_obj.weekday()
                download_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                index_data_list.append(IndexData(name, value, date_str, download_date, dayofweek))

        return index_data_list

    def ret_index_symbol_list(self):
        rlist = ['SP500', 'NASDAQ100']
        return rlist
    
    def ret_index_symbol_list2(self):
        return list(self.symbols.keys())


class DatabaseManager:
    def __init__(self, db_name='index_history.sqlite'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS indices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    value REAL NOT NULL,
                    date TEXT NOT NULL, 
                    download_date TEXT NOT NULL,
                    dayofweek INTEGER NOT NULL,
                    UNIQUE(symbol, date)
                )
            ''')

    def insert_index_data(self, index_data_list):
        with self.conn:
            self.conn.executemany('''
                INSERT OR REPLACE INTO indices (symbol, value, date, download_date, dayofweek) VALUES (?, ?, ?, ?, ?)
            ''', [(data.symbol, data.value, data.date, data.download_date, data.dayofweek) for data in index_data_list])

    def get_latest_value_of_week(self, symbol, today):
        with self.conn:
            cursor = self.conn.execute('''
                SELECT value 
                FROM indices 
                WHERE symbol = ? AND date <= ?
                ORDER BY date DESC 
                LIMIT 1
            ''', (symbol, today))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_all_period(self, symbol):  
        with self.conn:
            cursor = self.conn.execute('''
                SELECT DISTINCT date, value, dayofweek
                FROM indices 
                WHERE symbol = ?
                ORDER BY date
            ''', (symbol,))
            result = cursor.fetchall()
            rows = []
            for row in result:
                rdict = {'date': row[0], 'value': row[1], 'dayofweek': row[2] }
                rows.append(rdict)
            return rows
        
    def get_week_rows(self, symbol, monday_str, today_str):
        
        with self.conn:
            cursor = self.conn.cursor()        
            query = '''
            SELECT * FROM indices
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
            '''
            cursor.execute(query, (symbol, monday_str, today_str))
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def get_value_by_date(self, symbol, date_str):
        with self.conn:
            cursor = self.conn.execute('''
                SELECT value 
                FROM indices 
                WHERE symbol = ? AND date = ?
            ''', (symbol, date_str))
            result = cursor.fetchone()
            # print(result)
            return result[0] if result else None


    def upload_forex_data(self, period='5d'):
 
        class ForexData:
            def __init__(self, symbol, rate, date):
                self.symbol = symbol
                self.rate = rate
                self.date = date
                self.dayofweek = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').weekday()

        def create_forex_table():
            # 為替データを保存するテーブルを作成
            with self.conn:
                cursor = self.conn.execute("""
                CREATE TABLE IF NOT EXISTS forex_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    rate REAL NOT NULL,
                    date TEXT NOT NULL,
                    dayofweek INTEGER NOT NULL,
                    UNIQUE(symbol, date)
                )
                """)

        def insert_forex_data(forex_data_list):
            with self.conn:
                self.conn.executemany('''
                    INSERT OR REPLACE INTO forex_rates (symbol, rate, date, dayofweek) VALUES (?, ?, ?, ?)
                ''', [(data.symbol, data.rate, data.date, data.dayofweek) for data in forex_data_list])


        # `yfinance` を使って USD/JPY のデータを取得
        usd_jpy = yf.Ticker("JPY=X")
        data = usd_jpy.history(period=period)
        create_forex_table()
        # print(data)
        # 最新の為替レートを取得
        if not data.empty:
            forex_data_list = []
            for row in data.itertuples():
                # print(f"インデックス: {row.Index}, 行データ: {row.Close}")
                date_str = row.Index.strftime('%Y-%m-%d %H:%M:%S')
                latest_rate = row.Close
                forex_data_list.append(ForexData('USD/JPY', latest_rate, date_str) )
                
            insert_forex_data(forex_data_list)
            print(f"保存完了: USD/JPY = {latest_rate:.3f} ({date_str})")
        else:
            print("為替データの取得に失敗しました")

    def get_forex_data(self):
        """
        為替レートデータを取得し、欠損値を直前の値で補完して返す
        :return: 日付をキーとした為替レートの辞書
        """

        def get_forex_table():
            # 為替データを保存するテーブルを作成
            with self.conn:
                cursor = self.conn.execute("""
                    SELECT date, rate, dayofweek FROM forex_rates
                    WHERE symbol = 'USD/JPY'
                    ORDER BY date
                """)
                rows = cursor.fetchall()
                return rows

        def date_complementdate(rows):
            """為替データの日付は歯抜けなので補間する
            """
            first_row_date_str = rows[0][0]
            start_date = datetime.strptime(first_row_date_str, '%Y-%m-%d %H:%M:%S') 
            last_row_date_str = rows[-1][0]
            end_date = datetime.strptime(last_row_date_str, '%Y-%m-%d %H:%M:%S') 
            
            forex_data_dict = {}
            for row in rows:
                date_str = row[0]
                rate = row[1]
                dayofweek = row[2]
                current_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') 
                forex_data_dict[date_str] = {'date': current_date, 'rate': rate, 'dayofweek': dayofweek}

            # print(forex_data_dict)
            tmp_ratio = 0
            for i in range((end_date - start_date).days + 1):
                date = start_date + timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d %H:%M:%S')
                weekday = date.weekday()
                
                if date_str in forex_data_dict:
                    # データが存在する場合
                    tmp_row = forex_data_dict[date_str]
                    tmp_ratio = tmp_row['rate']
                else:
                    forex_data_dict[date_str] = {'date': date, 'rate': tmp_ratio, 'dayofweek': weekday}
            
            return forex_data_dict

        # 日付をキーとした辞書を作成
        rows = get_forex_table()
        forex_data_dict = date_complementdate(rows)
        # exit()
        return forex_data_dict

    def close(self):
        self.conn.close()


# DatabaseManager クラスし尻尾


if __name__ == "__main__":
    
    args = ou.get_date_option()
    period = args.po
    fetcher = IndexFetcher()
    
    index_data_list = fetcher.fetch(period=period)

    db_manager = DatabaseManager()
    db_manager.insert_index_data(index_data_list)
    db_manager.close()




