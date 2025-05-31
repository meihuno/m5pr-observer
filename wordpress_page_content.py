from datetime import datetime, timedelta
from daytime_util import DayTimeUtil

MINUS_5PERCENT_RULE = -5.0

class WordPressPageContent(object):
    """WordpresのHTMLを生成する。コンテンツをそのままタグで包むようにする。なるべく。"""

    def __init__(self):
        self.day_map = {
            'Monday': '月曜日',
            'Tuesday': '火曜日',
            'Wednesday': '水曜日',
            'Thursday': '木曜日',
            'Friday': '金曜日',
            'Saturday': '土曜日',
            'Sunday': '日曜日'
        }
        self.dtu = DayTimeUtil()

    def _ret_today_state(self, today):
        today_str1 = self.dtu.ret_ymd_string(today)
        daystring = self.dtu.ret_daystring(today)
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        today_line = f'今日は<strong>{today_str1}</strong>、<strong>{daystring}</strong>です。(Update: {now_str})'
        return today_line

    def _ret_red_tag(self):
        open1 = '<mark style=\"background-color:rgba(0, 0, 0, 0);color:#f62b01\" class=\"has-inline-color\">'
        close1 = '</mark>'
        return open1, close1

    def _ret_stockchart_url_link(self, key):
        rstr = ''
        if key == 'SP500':
            rstr = '<p>SP500のスコアは<a href="https://stockcharts.com/sc3/ui/?s=%24SPX">stockchartsを$SPXで検索する</a>からも確認できます。</p>'
        elif key == 'NASDAQ100':
            rstr = '<p>NASDAQ100のスコアは<a href="https://stockcharts.com/sc3/ui/?s=%24NDX">stockchartsを$NDXで検索する</a>ことでも確認できます。</p>'
        elif key == 'both':
            rstr = '<p>SP500のスコアは<a href="https://stockcharts.com/sc3/ui/?s=%24SPX">stockchartsを$SPXで検索する</a>からも確認できます。NASDAQ100のスコアは<a href="https://stockcharts.com/sc3/ui/?s=%24NDX">stockchartsを$NDXで検索する</a>ことでも確認できます。</p>'
        return rstr

    def ret_conclusion_state(self, key, percentage_change):
        conclusion_state = ''

        if percentage_change < MINUS_5PERCENT_RULE:
            conclusion_state += f"<strong>{key}はマイナス5%ルール発動中です！</strong>"

        if conclusion_state == '':
            conclusion_state = '今日は<strong>マイナス5%ルール、発動しませんでした</strong>。よい週末をお過ごしください。'
        else:
            link_line = """<p><strong>時は来たッ！！ いざ！ </strong><a href="https://www.rakuten-sec.co.jp/ITS/V_ACT_Login.html">楽天証券</a> or <a href="https://www.sbisec.co.jp/contents/">SBI証券</a>  へ<strong>Go！！</strong></p>"""
            conclusion_state += link_line
    
        return conclusion_state

    def _ret_site_statement_old(self):
        site_statement = '本サイトは「<bold>投資塾ゆう</bold>」さんが提唱された「<strong>▲（マイナス）5%ルール</strong>」投資法を実践することを目的として、<strong>SP500</strong>と<strong>NASDAQ100</strong>指数が<strong>先週金曜日から5%下落しているか(ルール発動条件)</strong>を表示します。<br>'
        return site_statement

    def _ret_site_statement(self):
        site_statement = '本サイトはSP500やNASDAQ100の騰落率を見て一喜一憂することを目的として、<strong>SP500</strong>と<strong>NASDAQ100</strong>指数が<strong>先週金曜日から5%下落しているか(ルール発動条件)</strong>を表示しています。<br>'
        return site_statement

    def ret_weekday_content(self, today, status_dict):
        
        def ret_conclusion_state(status_dict):
            conclusion_state = ''
            for key, stats_list in status_dict.items():
                percentage_change = stats_list[-1]['percentage_change']
                if percentage_change < MINUS_5PERCENT_RULE:
                    conclusion_state += f'{key}で5%ルール発動中です。'
            
            if conclusion_state == '':
                conclusion_state = '今日は5%ルール発動していません。今週のSP500とNASDAQ100の推移を示します。'
        
            return conclusion_state

        result_state = ret_conclusion_state(status_dict)
        today_state = self._ret_today_state(today)
        site_statement = self._ret_site_statement()

        def ret_weekday_table_row_lines(day_status_list):
            rlines = []
            for content_dict in day_status_list:
                day = content_dict['day']
                value = content_dict['value']
                updown = content_dict['updown']
                status = content_dict['status']
                threshold = content_dict['threshold']

                # FIXME: サボった。本来content_dicな内にUpdonw情報は持っているべき
                tag1, close1 = self._ret_red_tag()
                if '(Down)' in updown:
                    # FIXME weekendと共通にするべき
                    if '発動せず' in status:
                        tr_line = f"""<tr><td>{day}</td><td>{value}</td><td>{tag1}{updown}{close1}</td><td>{status}</td><td>{threshold}</td></tr>"""
                    else:
                        tr_line = f"""<tr><td>{day}</td><td>{value}</td><td>{tag1}{updown}{close1}</td><td>{tag1}{status}{close1}</td><td>{threshold}</td></tr>"""
                else:
                    tr_line = f"""<tr><td>{day}</td><td>{value}</td><td>{updown}</td><td>{status}</td><td>{threshold}</td></tr>"""
                
                rlines.append(tr_line)

            rstr = '\n'.join(rlines)
            return rstr

        def ret_each_index_weekday_table_lines(key, day_status_dict):
            """各indexごとの週の推移を示すテーブル"""

            tr_lines = ret_weekday_table_row_lines(day_status_dict)

            line = f"""
            <figure class="wp-block-table">
            <table>
            <thead><tr><th>Day</th><th>スコア</th><th>UpDown（先の金曜と比較）</th><th>ルール発動？</th><th>ルール発動ライン</th></tr></thead>
            <tbody>
            {tr_lines}
            </tbody>
            </table>
            <figcaption class="wp-element-caption">今週の{key}の推移</figcaption></figure>
            """

            return line


        def ret_weekday_table(status_dict):
            rlist = []
            for key, content_dict in status_dict.items():
                
                table_line = ret_each_index_weekday_table_lines(key, content_dict)
                rline = f"""
                <!-- wp:paragraph -->
                <p><strong>{key}</strong></p>
                {self._ret_stockchart_url_link(key)}
                <!-- /wp:paragraph -->
                
                <!-- wp:table -->
                {table_line}
                <!-- /wp:table -->
                """
                rlist.append(rline)

            rstr = ''.join(rlist)
            return rstr
        
        table_line = ret_weekday_table(status_dict)

        rline = f"""

        <!-- wp:paragraph -->        
        <p>{site_statement}</p> <p>{today_state} {result_state}</p>
        <!-- /wp:paragraph -->

        {table_line}
        """

        return rline
    
    def ret_weekend_content(self, today, status_dict):

        def ret_conlusion_state(state_dict):
            
            conclusion_state = ''
            for key, stats in state_dict.items():
                percentage_change = stats['percentage_change']
                if percentage_change < MINUS_5PERCENT_RULE:
                    conclusion_state += f"<strong>{key}はマイナス5%ルール発動中です！</strong>"

            if conclusion_state == '':
                conclusion_state = '今日は<strong>マイナス5%ルール、発動しませんでした</strong>。よい週末をお過ごしください。'
            else:
                link_line = """<p><strong>時は来たッ！！ いざ！ </strong>楽天証券 or SBI証券へ<strong>Go！！</strong></p>"""
                conclusion_state += link_line

            return conclusion_state
        
        result_state = ret_conlusion_state(status_dict)
        today_state = self._ret_today_state(today)
        site_statement = self._ret_site_statement()

        def ret_weekend_row(status_dict):
            rlist = []
            print(status_dict)
            for key, stats in status_dict.items():
                value = stats['value']
                past_value = stats['past_value']
                updown = stats['updown']
                result = stats['status']

                tr_line = ret_tr_line(key, value, past_value, updown, result)
                rlist.append(tr_line)
            rstr = ''.join(rlist)
            return rstr

        def ret_tr_line(key, value, past_value, updown, result):
            # FIXME. サボった。本来content_dicな内にUpdonw情報は持っているべき。weekendとweekdayとで共通のメソッドにするべき
            tag1, close1 = self._ret_red_tag()
            if '(Down)' in updown:
                # この辺のロジックも整すする必要あり。複雑になると破綻する。
                if not '発動せず' in result:
                    tr_line = f"""<tr><td>{key}</td><td>{past_value}</td><td>{tag1}{value}{close1}</td><td>{tag1}{updown}{close1}</td><td>{tag1}{result}{close1}</td></tr>"""
                else:
                    tr_line = f"""<tr><td>{key}</td><td>{past_value}</td><td>{tag1}{value}{close1}</td><td>{tag1}{updown}{close1}</td><td>{result}</td></tr>"""                    

            else:
                tr_line = f"""<tr><td>{key}</td><td>{past_value}</td><td>{value}</td><td>{updown}</td><td>{result}</td></tr>"""

            return tr_line

        def ret_weekend_table_lines(status_dict):
        
            tr_lines = ret_weekend_row(status_dict)

            rline = f"""
            <!-- wp:table -->
            <figure class="wp-block-table">
            <table><thead><tr><th>index</th><th>先週のスコア</th><th>今週金曜日スコア</th><th>先週比UpDown</th><th>▲5%ルール発動した？</th></tr></tはhead>
            <tbody>
            {tr_lines}
            </tbody>
            </table>
            <figcaption class="wp-element-caption">今週のステータス</figcaption></figure>
            <!-- /wp:table -->
            """
            return rline

        table_line = ret_weekend_table_lines(status_dict)

        rline = f"""

        <!-- wp:paragraph -->        
        <p>{site_statement}</p>
        <!-- /wp:paragraph -->

        <!-- wp:paragraph -->        
        <p>{today_state}</p><p>{result_state}</p>
        <!-- /wp:paragraph -->

        <!-- wp:table -->
        {table_line}
        <!-- /wp:table -->

        <!-- wp:paragraph -->
        {self._ret_stockchart_url_link('both')}
        <!-- /wp:paragraph -->
        """

        return rline



