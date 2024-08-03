from argparse import ArgumentParser

def get_date_option():
    argparser = ArgumentParser()
    argparser.add_argument('--po', '--period-option', type=str,
                           default='1d',
                           help='1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max')
    return argparser.parse_args()

def get_phase_option():
    argparser = ArgumentParser()
    argparser.add_argument('--phase', '--phase-switch', type=str,
                           default='deploy',
                           help='test or deploy')
    argparser.add_argument('--date', '--date', type=str,
                           default='none',
                           help='target date')
    return argparser.parse_args()