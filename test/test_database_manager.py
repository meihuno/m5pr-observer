# test/test_database_manager.py
"""リファクタリング時にテストを追加です。
"""
import unittest
import sys
import os

# カレントディレクトリをsys.pathに追加してインポート可能にする
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download_stock_info import IndexFetcher, DatabaseManager  # カレントディレクトリのモジュールをインポート

class TestDatabaseManager(unittest.TestCase):
    
    def setUp(self):
        # テストケースごとに初期化処理が必要な場合に記述（任意）
        self.fetcher = IndexFetcher()
        self.db_manager = DatabaseManager()
        pass
    
    def test_get_value_by_date(self):
        # get_value_by_date 関数のテスト
        ok_date = "2025-02-28 00:00:00"
        ng_date = "1999-03-01 00:00:00"
        for symbol in self.fetcher.symbols:
            ok_value = self.db_manager.get_value_by_date(symbol, ok_date)
            none_value = self.db_manager.get_value_by_date(symbol, ng_date)
            print([symbol, ok_value, none_value])
            self.assertIsNone(none_value)
            self.assertIsNotNone(ok_value)

if __name__ == '__main__':
    unittest.main()