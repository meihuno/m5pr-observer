from download_stock_info import IndexFetcher, DatabaseManager
import option_util as ou
import pandas as pd
from datetime import datetime

class IndexComposeTickers(object):

    def _ret_index_companies(self, symbol="hoge"):
        # WikipediaからS&P500銘柄リストを取得
        if symbol == 'SP500':
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            sp500_df = pd.read_html(url)[0]
            tickers = sp500_df['Symbol'].tolist()
            print(tickers)
        elif symbol == 'NASDAQ100':
            url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
            nasdaq_df = pd.read_html(url)[4]  # 2025年5月時点では表番号4
            tickers = nasdaq_df['Ticker'].tolist()
            print(tickers)

class PERPBR(object):

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

        # 1996年以降抽出
        # df = df['1900':]
        return df

if __name__ == "__main__":
    
    args = ou.get_date_option()
    period = args.po
    fetcher = IndexFetcher()
    
    box = PERPBR()
    box.ret_sp500_per_df()
    