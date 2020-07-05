import os

PATHS = {}
PATHS['base'] = os.path.dirname(os.path.abspath(__file__))
PATHS['css'] = os.path.join(PATHS['base'], 'theme.css')
PATHS['data'] = os.path.join(PATHS['base'], 'data')
PATHS['asos'] = os.path.join(PATHS['data'], 'asos_meta.pkl')
PATHS['newborns'] = os.path.join(PATHS['data'], 'newborns.db')
PATHS['tmp'] = os.path.join(PATHS['data'], 'tmp_ds.npy')

FMTS = {}
FMTS['daily_asos'] = (
    'https://mesonet.agron.iastate.edu/'
    'cgi-bin/request/daily.py?'
    'network={network}&stations={station}&'
    'year1=1928&month1=1&day1=1&'
    'year2=2020&month2=12&day2=1'
)

CLRS = {
    'light_pink': '#ffd3d4',
    'stale_blue': '#a3b8cd',
    'white': '#e5e5e5',
    'gray': '#5B5B5B',
    'red': '#d44642',
    'blue': '#87b6bc',
    'yellow': '#F6CA06',
    'dark_brown': '#8c520a',
    'light_tan': '#f5e7c1',
    'fresh_blue': '#7eccba',
    'sky_blue': '#41b7c4',
    'sea_blue': '#5bb5ae',
    'green_blue': '#01665e',
    'white_smoke': '#f5f5f5'
}
