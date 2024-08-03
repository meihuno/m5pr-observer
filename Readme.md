# マイナス5%ルール観測所用pythonコード

## 概要

本ドキュメントは「ゆうさんの投資塾」（https://www.youtube.com/@toushijukuyou）で教わったマイナス5%ルールの投資法を実践するためのサポートサイト「▲（マイナス）5%ルール観測所（https://m5pr-observer.com/）」（以下、本サイト）のバックエンドツールについて記載する。本バックエンドツールは以下の機能を提供する。

 - SP500およびNASDAQ100指数の情報をDB(sqlite)に格納する
 - DBのSP500およびNASDAQ100指数情報でWordpressのHTMLテーブルを更新する

### Require

以下のpythonライブラリをインストールすること。

yfinance
python-wordpress-xmlrpc

以下の環境変数をセットすること。

WORDPRESS_USERNAME
WORDPRESS_PASSWORD

動作確認はpython3.8.12で行った。3.9以降でも動くと思う（検証はしていない）。

### 使い方

以下のコマンドをserver上でcronで定時実行し、サイトを自動更新する。

インデックス情報を取得してDB(./index_history.sqlite)に格納。

```
usage: download_stock_info.py [-h] [--po PO]

optional arguments:
  -h, --help            show this help message and exit
  --po PO, --period-option PO
                        1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
```

WordpressのホームページにUploadする。https://m5pr-observer.com/の構造に依拠している。

```
usage: gogo_update_wordpress_index_page.py [-h] [--phase PHASE] [--date DATE]

optional arguments:
  -h, --help            show this help message and exit
  --phase PHASE, --phase-switch PHASE
                        test or deploy
  --date DATE, --date DATE
                        target date
```

### コードの責務（リファクタリングが必要）

download_stock_info.py: DBへの格納

wordpress_page_content.py : Wordpressのコンテンツを作成

wordpress_page_content_maker.py : DBのインデックス情報を加工するロジック（先週から5%下落したらルール発動など）

edit_wordpress.py : WordPressへのアクセス

option_util.py: コマンドラインオプション

gogo_update_wordpress_index_page.py : サイト更新
