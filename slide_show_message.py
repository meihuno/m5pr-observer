class WordpressLightningSlideShowMessage:
    
    def __init__(self):
        self.default_message = {
            'title': 'Welcome',
            'text': 'This is a sample message',
            'button_text': 'Learn More',
            'button_url': '#'
        }

    def _ret_main_message(self, key, percentage_change):
        percentage = str(round(percentage_change, 3))
        one_line = f'{key} <mark style="color:#f62b01" class="has-inline-color">{percentage}%↓</mark>'
        return one_line
    
    def get_slide_content(self, params=None):
        """
        スライドショーの内容を生成して返す
        params: dict 
            - title: スライドのタイトル
            - text: スライドの本文
            - button_text: ボタンのテキスト
            - button_url: ボタンのリンク先URL
        """
        if params is None:
            params = self.default_message

        main_message = "マイナス5%ルール発中中！！\n"
        for key, sub_dict in params.items():
            main_message += self._ret_main_message(key, sub_dict['percentage_change']) + "\n"

        pass

    def create_multiple_slides(self, slides_params):
        """
        複数のスライドを生成
        slides_params: list[dict] スライドのパラメータリスト
        """
        return [self.get_slide_content(params) for params in slides_params]