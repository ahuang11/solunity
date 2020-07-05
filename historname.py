import sqlite3

import param
import panel as pn
import pandas as pd
import hvplot.pandas
import holoviews as hv

import constant as C

QUERY_RANDOM_FMT = '''
    SELECT name FROM newborns_name_year_gender
    INNER JOIN newborns_name_max USING(name)
    WHERE newborns_name_year_gender.percent_male >= ?
    AND newborns_name_year_gender.percent_male <= ?
    AND newborns_name_max.max >= ?
    AND newborns_name_max.max <= ?
    AND name LIKE ?
    ORDER BY RANDOM() LIMIT 1;
'''

QUERY_NAME_FMT = '''
    SELECT *
    FROM newborns_name_year_gender
    INNER JOIN newborns_total USING(year)
    WHERE newborns_name_year_gender.name == ?
'''

DF_COLS = ['Name', 'Year', 'Female', 'Male', 'Count',
           'Cumulative Count', 'Percent Male',
           'Total', 'Cumulative Total']


class Historname(param.Parameterized):
    names = param.String()
    gender = param.Selector(objects=['All', 'Both', 'Female', 'Male'])
    prange = param.Range(default=(0, 100000), bounds=(0, 100000))
    random = param.Action(label='Random')

    _stream = hv.streams.PointerX()
    _opts = hv.opts.defaults(
        hv.opts.Area(
            responsive=True,
            line_color='white',
            line_alpha=0.8,
            line_width=0.05,
            alpha=0.85,
        ),
        hv.opts.Curve(
            responsive=True,
            line_color='gray',
            line_width=0.5,
        ),
        hv.opts.Overlay(
            responsive=True, show_grid=True, padding=0,
            legend_position='top_right', fontscale=1.5,
            toolbar='disable'
        ),
        hv.opts.Text(
            responsive=True, show_grid=False, padding=0,
            text_alpha=0.5, fontscale=1.5, toolbar='disable'
        )
    )

    widgets = param.Parameter()

    def __init__(self):
        super().__init__()
        self.holoviews = pn.pane.HoloViews(
            min_height=500, max_height=800, max_width=1000,
            sizing_mode='stretch_both', align='center')
        self.random = self.random_name
        self.names_row = pn.Param(
            self,
            parameters=['names'],
            widgets={
                'names': {'name': '',
                          'placeholder': ('Enter a name here; '
                                          'wildcards (*) supported!'),
                          'height': 38},
            },
            align='center', sizing_mode='stretch_width'
        )
        self.random_row = pn.Row(*pn.Param(
            self,
            parameters=['random', 'gender'],
            widgets={
                'random': {'sizing_mode': 'stretch_width'},
                'gender': {'type': pn.widgets.RadioButtonGroup,
                           'sizing_mode': 'stretch_width'},
            },
            align='center', sizing_mode='stretch_width'
        )[1:], align='center', sizing_mode='stretch_width')
        self.prange_row = pn.Param(
            self,
            parameters=['prange'],
            widgets={
                'prange': {'name': 'Peak Popularity',
                           'sizing_mode': 'stretch_width',
                           'margin': (5, 16)}
            }
        )
        self.widgets = pn.Column(
            *self.names_row[1:], self.random_row, *self.prange_row[1:],
            align='center', sizing_mode='stretch_width', max_width=800
        )
        self.markdown = pn.pane.Markdown(sizing_mode='stretch_width')
        self.random_name(None)

    @staticmethod
    def execute_query(query, inputs):
        with sqlite3.connect(C.PATHS['newborns']) as con:
            resp = con.execute(query, inputs)
        return resp

    def random_name(self, event, names='%'):
        if self.gender == 'All':
            percent_male = (0, 1)
        elif self.gender == 'Male':
            percent_male = (0.7, 1)
        elif self.gender == 'Both':
            percent_male = (0.3, 0.7)
        else:
            percent_male = (0, 0.3)

        if self.names:
            names = self.names
        names = names.replace('*', '%').strip()
        inputs = (percent_male[0], percent_male[1],
                  self.prange[0], self.prange[1], names)
        resp = self.execute_query(QUERY_RANDOM_FMT, inputs)
        try:
            self.names_sel = resp.fetchone()[0]
        except TypeError:
            self.names_sel = 'Unavailable'
        self.plot(names=self.names_sel)

    @pn.depends(_stream.param.x)
    def text(self, year):
        if len(self.df_names) == 0:
            return self.markdown

        if year is not None:
            year = int(year)

        if year not in self.df_names.index:
            year = self.df_names.index.min()

        row = self.df_names.loc[year]
        total = row['Total']
        count = row['Count']
        pct_total = row['Percent Total']

        males = row['Male']
        pct_males = row['Percent Male']

        females = row['Female']
        pct_females = 1 - row['Percent Male']

        cumulative_total = row['Cumulative Total']
        cumulative_count = row['Cumulative Count']
        pct_cumulative = row['Percent Cumulative']

        self.markdown.object = f"""
            <center><p>
            In {year}, there were {total:,} newborns born
            in the United States.<br>On public record,
            {count:,} ({pct_total:.3%}) of these newborns were
            named {self.names_sel}; {pct_males:.1%} were male while
            {pct_females:.1%} were female.<br>Overall, from 1880 to
            {year}, there were {cumulative_count:,} {self.names_sel}'s;
            that's {pct_cumulative:.3%} of {cumulative_total:,}
            newborns since 1880!<br>Download the data
            <a href="https://catalog.data.gov/dataset/
            baby-names-from-social-security-card-applications-
            national-level-data" target="_blank">here</a>!
            </center></p>
        """
        return self.markdown

    @param.depends('names', watch=True)
    def plot(self, names=None):
        if names is None and ('*' in self.names or '%' in self.names):
            self.random_name(None, names=self.names)
            return

        resp = self.execute_query(QUERY_NAME_FMT, (self.names_sel,))
        self.df_names = pd.DataFrame(resp, columns=DF_COLS).set_index('Year')
        self.df_names['Percent Total'] = (
            self.df_names['Count'] / self.df_names['Total'])
        self.df_names['Percent Cumulative'] = (
            self.df_names['Cumulative Count'] /
            self.df_names['Cumulative Total']
        )

        if len(self.df_names) > 0:
            peak = self.df_names['Count'].max()
            if peak < 100:
                peak = 100

            text = hv.Text(
                1885, peak - peak / 20, self.names_sel,
                halign='left', valign='top', fontsize=35
            )
            color = [C.CLRS['stale_blue'], C.CLRS['light_pink']]
            area = self.df_names.hvplot.area(
                x='Year',
                y=['Male', 'Female'],
                color=color,
                stacked=True
            )
            line = self.df_names.hvplot.line(
                x='Year',
                y='Count',
                hover_cols=['Male', 'Female', 'Count']
            )
            overlay = text * area * line
        else:
            peak = 100
            text = hv.Text(
                0.5, 0.5, self.names_sel,
                halign='center', valign='center', fontsize=35
            ).opts(xaxis='bare', yaxis='bare')
            overlay = text

        overlay = overlay.opts(ylabel='', xlabel='', title='',
                               xlim=(1880, 2018), ylim=(0, peak))
        self._stream.source = overlay
        self.holoviews.object = overlay

    def view(self):
        pink = C.CLRS['light_pink']
        blue = C.CLRS['stale_blue']
        title = pn.pane.Markdown(f'''
            <center>
            <span style="color: {pink}; font-size:35px">Histor</span>
            <span style="color: {blue}; font-size:35px">name</span>
            | Find how popular a name is historically.
            </center>
            ''', sizing_mode='stretch_width', margin=(-10, 10)
        )
        layout = pn.Column(
            title, self.widgets, self.holoviews, self.text,
            sizing_mode='stretch_both')
        return layout
