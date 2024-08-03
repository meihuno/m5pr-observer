
class WordPressPageContent(object):
    """WordpresのHTMLを生成する。コンテンツをそのままタグで包むようにする。なるべく。"""

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

    def ret_weekday_content(self, site_statement, today_state, result_state, status_dict):
        
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
        #  <p>{site_statement}</p> <p>{today_state} {result_state}</p>
        rline = f"""

        <!-- wp:paragraph -->        
        <p>{site_statement}</p> <p>{today_state} {result_state}</p>
        <!-- /wp:paragraph -->

        {table_line}
        """

        return rline
        

    def ret_weekend_content(self, site_statement, today_state, result_state, status_dict):

        def ret_weekend_row(status_dict):
            rlist = []
            print(status_dict)
            for key, stats in status_dict.items():
                value = stats['value']
                past_value = stats['past_value']
                updown = stats['updown']
                result = stats['result']

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



