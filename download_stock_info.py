import sqlite3
from datetime import datetime, timedelta
import json
import yfinance as yf
from dateutil import parser
import pprint as pp
import option_util as ou
from edit_wordpress import EditWordPress
from wordpress_page_content import WordPressPageContent

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
            # 'NASDAQ': '^IXIC',
        }
        self.stockchats_urls = {
            'SP500' :'https://stockcharts.com/sc3/ui/?s=%24SPX',
            'NASDAQ100': 'https://stockcharts.com/sc3/ui/?s=%24NDX', 
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

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    
    args = ou.get_date_option()
    period = args.po
    fetcher = IndexFetcher()
    
    index_data_list = fetcher.fetch(period=period)
    db_manager = DatabaseManager()
    db_manager.insert_index_data(index_data_list)
    db_manager.close()

    


