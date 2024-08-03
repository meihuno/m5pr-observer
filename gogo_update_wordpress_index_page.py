import sqlite3
from datetime import datetime, timedelta
import json
import yfinance as yf
from dateutil import parser
import pprint as pp
import option_util as ou
from edit_wordpress import EditWordPress
from wordpress_page_content_maker import WordPressPageContentMaker

if __name__ == "__main__":
    
    args = ou.get_phase_option()
    phase = args.phase
    datestr = args.date
    if phase == 'test' and ( not datestr == 'none'):
        gogo_wordpress_edit = WordPressPageContentMaker(phase=phase, datestr=datestr)
    else:
        gogo_wordpress_edit = WordPressPageContentMaker()
    rline = gogo_wordpress_edit.ret_content_of_today()
    # pp.pprint(rline)

    box = EditWordPress()
    box.gogo_edit_page(body=rline)