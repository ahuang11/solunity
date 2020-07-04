import param
import panel as pn
import holoviews as hv

from historname import Historname
from weatherflash import WeatherFlash
from colordropper import ColorDropper
import constant as C


APP_NAMES = ['Historname', 'WeatherFlash', 'ColorDropper']

pn.extension(css_files=[C.PATHS['css']])
hv.renderer('bokeh').theme = 'caliber'


def initialize(event):
    progress = pn.widgets.Progress(active=True, sizing_mode='stretch_width',
                                   max_width=500, align='center')
    dashboard.objects = [vspace, progress, vspace]
    if event.obj.name == 'Historname':
        dashboard.objects = [Historname().view()]
    elif event.obj.name == 'WeatherFlash':
        dashboard.objects = [WeatherFlash().view()]
    elif event.obj.name == 'ColorDropper':
        dashboard.objects = [ColorDropper().view()]


vspace = pn.layout.VSpacer()
title = pn.pane.Markdown(
    '# <center>Solunity</center>',
    sizing_mode='stretch_width', margin=(-25, 10)
)
subtitle = pn.pane.Markdown("""
    <center><p>Apps designed by Andrew Huang;
    click a button below to begin.</p></center>
    """, sizing_mode='stretch_width'
)
caption = pn.pane.Markdown("""
    <p><center>
    <a href="https://github.com/ahuang11/solunity" target="_blank">Source Code</a> |
    <a href="https://github.com/ahuang11/" target="_blank">My GitHub</a><br>
    Made possible with
    <a href="https://www.python.org/" target=_blank">Python</a>,
    <a href="https://pandas.pydata.org/" target=_blank">pandas</a>,
    <a href="https://xarray.pydata.org/" target=_blank">xarray</a>,
    <a href="https://numpy.org/" target=_blank">numpy</a>,
    <a href="https://panel.holoviz.org/" target=_blank">panel</a>,
    <a href="https://bokeh.org/" target=_blank">bokeh</a>,
    <a href="http://holoviews.org/" target=_blank">holoviews</a>, and
    <a href="https://dashboard.heroku.com/" target=_blank">Heroku</a>.<br>
    </p></center>
    """, sizing_mode='stretch_width'
)
buttons = [
    pn.widgets.Button(
        name=name, align='center', max_width=500
    )
    for name in APP_NAMES
]
for button in buttons:
    button.param.watch(initialize, 'clicks')

dashboard = pn.Column(
    vspace, title, subtitle, *buttons, caption, vspace,
    sizing_mode='stretch_both'
).servable(title='Solunity')
