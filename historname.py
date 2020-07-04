import glob

import param
import panel as pn
import pandas as pd
import hvplot.pandas
import holoviews as hv

import constant as C


# read just once
df = pd.concat(
    pd.read_pickle(fi) for fi in
    sorted(glob.iglob(C.PATHS['newborns']))
)


class Historname(param.Parameterized):
    names = param.String()
    gender = param.Selector(objects=['All', 'Either', 'Female', 'Male'])
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
            min_height=600, sizing_mode='stretch_both')
        self.random = self.random_name
        self.names_row = pn.Param(
            self,
            parameters=['names'],
            widgets={
                'names': {'name': '', 'placeholder': 'Enter a name here!',
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
        self.widgets = pn.Column(
            *self.names_row[1:], self.random_row,
            align='center', sizing_mode='stretch_width', max_width=800
        )
        self.markdown = pn.pane.Markdown(sizing_mode='stretch_width')

        self.df = df
        self.random_name(None)

    def random_name(self, event):
        if self.gender != 'All':
            if self.gender == 'Male':
                gender_subset = self.df['Percent Male'] > 0.75
            elif self.gender == 'Either':
                gender_subset = (
                    (self.df['Percent Male'] > 0.2) &
                    (self.df['Percent Male'] < 0.8)
                )
            else:
                gender_subset = self.df['Percent Male'] < 0.25
            series = self.df.loc[gender_subset, 'Name']
        else:
            series = self.df['Name']
        self.names = str(series.sample(n=1).values[0])

    @pn.depends(_stream.param.x)
    def text(self, year):
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
            named {self.names}; {pct_males:.1%} were male while
            {pct_females:.1%} were female.<br>Overall, from 1880 to
            {year}, there were {cumulative_count:,} {self.names}'s;
            that's {pct_cumulative:.3%} of {cumulative_total:,}
            newborns since 1880!</center></p>
        """
        return self.markdown

    @param.depends('names', watch=True)
    def plot(self):
        self.df_names = self.df.query(f'Name == "{self.names}"')
        self.year_min = self.df_names.index.min()
        self.year_max = self.df_names.index.max()
        peak = self.df_names['Count'].max()
        if peak < 100:
            peak = 100

        if len(self.df_names) > 0:
            text = hv.Text(
                1885, peak - peak / 20, self.names,
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
            text = hv.Text(
                0.5, 0.5, f'{self.names.title()} N/A',
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
