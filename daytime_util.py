from datetime import datetime, timedelta

class DayTimeUtil(object):

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

    def ret_daystring(self, today):
        daystring = today.strftime('%A')
        if daystring in self.day_map:
            daystring = self.day_map[daystring]        
        return daystring 
    
    def ret_ymd_string(self, today):
        today_str = today.strftime('%Y年%m月%d日')
        return today_str

    def ret_dateday_string(self, week_line, today):
        daystring = self.ret_daystring(today)
        today_str = self.ret_ymd_string(today)
        rstr = f'{week_line}の{daystring}({today_str})' 
        return rstr 
