import os
from io import BytesIO
from urllib.request import urlopen

import numpy as np
import panel as pn
import xarray as xr
import holoviews as hv
import matplotlib.pyplot as plt
from holoviews.streams import Tap
from bokeh.models.tools import WheelZoomTool
from matplotlib.colors import LinearSegmentedColormap

import constant as C
from util import remove_white_borders


IMAGE_URL = ('https://img06.deviantart.net/2635/i/2010/170/c/f/'
             'night_and_day_wallpaper_by_seph_the_zeth.jpg')
IMAGE_EXT = os.path.splitext(IMAGE_URL)[1]

DEFAULT_CMAP = 'RdBu_r'
NEW_LINE_INDENT = ',\n    '
HEXCODE = 'Hexcode'
RGB_1 = 'RGB (0 to 1)'
RGB_255 = 'RGB (0 to 255)'

STR_BOTH = 'stretch_both'
STR_WIDTH = 'stretch_width'
STR_HEIGHT = 'stretch_height'

EXAMPLE_CODE = """
```python
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap

ds = xr.tutorial.open_dataset('air_temperature').isel(time=0)

colors = [{colors}]

cmap = LinearSegmentedColormap.from_list(
    'my_cmap', colors, N=len(colors))
ds['air'].plot(x='lon', y='lat', cmap=cmap)
```
""".strip()


class ColorDropper(object):
    def show_image(self, ds):
        shape = ds['R'].shape
        aspect = shape[1] / shape[0]
        wheel_zoom = WheelZoomTool(zoom_on_axis=False)

        image = (
            hv.RGB(ds, ['X', 'Y'], ['R', 'G', 'B'])
        ).opts(
            'RGB', default_tools=['pan', wheel_zoom, 'tap', 'reset'],
            active_tools=['tap', 'wheel_zoom'], xaxis=None, yaxis=None,
            aspect=aspect, responsive=True, hooks=[remove_white_borders],
        ).opts(toolbar='above')

        tap = hv.streams.Tap(source=image, x=shape[1], y=shape[0])
        tap.param.watch(self.tap_update, ['x', 'y'])
        self.image_pane.object = image

    def read_data(self, input_obj, image_fmt, from_url):
        if from_url:
            content = urlopen(input_obj)
        else:
            content = BytesIO(input_obj)

        data = plt.imread(content, format=image_fmt)[::-1]
        self.pixelate_slider.end = int(max(data.shape) / 10)

        self.base_ds = xr.Dataset({
            'R': (('Y', 'X'), data[..., 0]),
            'G': (('Y', 'X'), data[..., 1]),
            'B': (('Y', 'X'), data[..., 2]),
        })

    def process_input(self, event):
        input_obj = event.new
        from_url = isinstance(input_obj, str)

        if from_url:
            image_fmt = os.path.splitext(input_obj)[1]
        else:
            image_fmt = os.path.splitext(self.file_input.filename)[1]

        if image_fmt == '':
            image_fmt = None

        self.read_data(input_obj, image_fmt, from_url)
        self.show_image(self.base_ds)

    @staticmethod
    def rgb_to_hexcode(r, g, b, to_255=False):
        clamp = lambda x: int(max(0, min(x, 255)))
        if to_255:
            r *= 255
            g *= 255
            b *= 255

        return '#{0:02x}{1:02x}{2:02x}'.format(
            clamp(r), clamp(g), clamp(b))

    @staticmethod
    def hexcode_to_rgb(hexcode, norm=False):
        code = hexcode.lstrip('#')
        if norm:
            values = (round(int(code[i:i + 2], 16) / 255, 4) for i in (0, 2, 4))
        else:
            values = (int(code[i:i + 2], 16) for i in (0, 2, 4))
        return str(tuple(values))

    def make_color_row(self, color):
        if self.embed_toggle.value and len(self.multi_select.options) > 0:
            value_str = f'<center>{color}</center>'
        else:
            value_str = ''

        if self.highlight_toggle.value:
            background = C.CLRS['white_smoke']
        else:
            background = None

        swath = pn.Row(
            pn.pane.HTML(value_str, background=background, height=18,
                         sizing_mode=STR_WIDTH),
            background=color, margin=0, sizing_mode=STR_WIDTH
        )

        if self.divider_toggle.value:
            divider = pn.Spacer(
                width=1, margin=0,
                background=C.CLRS['white_smoke'],
                sizing_mode=STR_HEIGHT
            )
            return pn.Row(swath, divider, margin=0)
        else:
            return swath

    def update(self, options):
        options = [
            opt for opt in options
            if opt != '' and
            len(opt) == 7 and
            opt.startswith('#')
        ]
        num_options = len(options)

        self.multi_select.options = options
        self.text_input.value = ', '.join(options)

        if num_options == 0:
            options = [C.CLRS['white_smoke']]

        self.color_row.objects = [self.make_color_row(opt) for opt in options]

        self.slider_update(None)

    def pixelate_update(self, event):
        num_pixels = self.pixelate_slider.value
        # similar to ds.coarsen(x=10).mean() but parameterized
        coarse_ds = getattr(
            self.base_ds.coarsen(
                **{'X': num_pixels, 'Y': num_pixels}, boundary='pad'
            ), self.pixelate_group.value.lower()
        )().astype(int)
        self.show_image(coarse_ds)

    def slider_update(self, event):
        options = self.multi_select.options.copy()

        num_options = len(options)
        if self.num_slider.value < num_options:
            self.num_slider.value = num_options
        self.num_slider.start = num_options

        if num_options == 1:
            options *= 2

        if num_options > 0:
            num_colors = self.num_slider.value
            interp_cmap = LinearSegmentedColormap.from_list(
                'interp_cmap', options, num_colors)
            interp_colors = [
                self.rgb_to_hexcode(*interp_cmap(i)[:3], to_255=True)
                for i in np.arange(interp_cmap.N)]
        else:
            interp_cmap = DEFAULT_CMAP
            interp_colors = options

        self.plot_pane.object = self.process_plot(interp_cmap)
        if self.output_group.value == HEXCODE:
            color_str = NEW_LINE_INDENT.join(f"'{opt}'" for opt in interp_colors)
        elif self.output_group.value == RGB_255:
            color_str = NEW_LINE_INDENT.join(
                self.hexcode_to_rgb(opt) for opt in interp_colors)
        elif self.output_group.value == RGB_1:
            color_str = NEW_LINE_INDENT.join(
                self.hexcode_to_rgb(opt, norm=True) for opt in interp_colors)

        color_str = '\n\t' + color_str + '\n'
        self.code_markdown.object = EXAMPLE_CODE.format(colors=color_str)

    def tap_update(self, x=0, y=0):
        self.previous_selections.append(self.multi_select.options)
        ds = self.image_pane.object.data
        try:
            sel_ds = ds.isel(X=round(x.new), Y=round(y.new))
            hexcode = self.rgb_to_hexcode(
                sel_ds['R'], sel_ds['G'], sel_ds['B'])
            options = self.multi_select.options + [hexcode]
            self.update(options)
        except (AttributeError, IndexError) as e:
            print(e)

    def remove_update(self, event):
        self.previous_selections.append(self.multi_select.options)
        options = [v for v in self.multi_select.options if v not in self.multi_select.value]
        self.update(options)

    def undo_update(self, event):
        options = self.previous_selections.pop(-1)
        self.update(options)

    def clear_update(self, event):
        self.previous_selections.append(self.multi_select.options)
        self.update([])

    def toggle_update(self, event):
        self.update(self.multi_select.options)

    def text_input_update(self, event):
        options = [color.strip() for color in event.new.split(',')]
        self.update(options)

    def process_plot(self, cmap):
        return self.hv_plot.opts(cmap=cmap)

    def view(self):
        # Initialize top side widgets
        horiz_spacer = pn.layout.HSpacer()

        random_colors = [
            f'#{integer:06x}' for integer in
            np.random.randint(0, high=0xFFFFFF, size=9)
        ]
        color_box = pn.GridBox(*[
            pn.pane.HTML(background=random_colors[i],
                         width=10, height=10, margin=1)
            for i in range(9)
        ], ncols=3, margin=(15, 0))

        title_markdown = pn.pane.Markdown(
            '# <center>ColorDropper</center>\n', margin=(5, 15, 0, 15))
        subtitle_markdown = pn.pane.Markdown(
            '### <center>(an online eyedropper tool)</center>',
            margin=(15, 0, 0, 0)
        )
        caption_markdown = pn.pane.Markdown(
            '<center><p>To use, paste an image url or click '
            'Choose File" to upload an image, then click on the image '
            'to get a hexcode for that clicked point!</p></center>',
            sizing_mode=STR_WIDTH, margin=0
        )

        # Create top side layout

        title_row = pn.Row(
            horiz_spacer,
            color_box,
            title_markdown,
            subtitle_markdown,
            horiz_spacer,
            sizing_mode=STR_WIDTH,
            margin=(0, 0, -15, 0))

        top_layout = pn.WidgetBox(
            title_row,
            caption_markdown,
            sizing_mode=STR_WIDTH,
        )

        # Initialize left side widgets

        url_input = pn.widgets.TextInput(placeholder='Enter an image url here!',
                                         margin=(15, 10, 5, 10))
        self.file_input = pn.widgets.FileInput(accept='image/*')

        self.pixelate_group = pn.widgets.RadioButtonGroup(
            options=['Mean', 'Min', 'Max'], margin=(15, 10, 5, 10))

        self.pixelate_slider = pn.widgets.IntSlider(
            name='Number of pixels to aggregate', start=1, end=100, step=1,
            sizing_mode=STR_WIDTH)
        self.pixelate_slider.callback_policy = 'throttled'

        self.text_input = pn.widgets.TextInput(
            placeholder='Click on image above to start or add '
                        'comma separated hexcodes here!',
            margin=(10, 10, 0, 10))

        self.divider_toggle = pn.widgets.Toggle(name='Show Divider',
                                           sizing_mode=STR_WIDTH)
        self.embed_toggle = pn.widgets.Toggle(name='Embed Values', value=True,
                                         sizing_mode=STR_WIDTH)
        self.highlight_toggle = pn.widgets.Toggle(name='Highlight Text',
                                             sizing_mode=STR_WIDTH)

        self.previous_selections = []
        self.multi_select = pn.widgets.MultiSelect(
            options=[], sizing_mode=STR_BOTH)
        remove_button = pn.widgets.Button(name='Remove', button_type='warning',
                                          width=280)
        undo_button = pn.widgets.Button(name='Undo', button_type='primary',
                                        width=280)
        clear_button = pn.widgets.Button(name='Clear', button_type='danger',
                                         width=280)
        self.image_pane = pn.pane.HoloViews(
            sizing_mode='scale_both', align='center',
            max_height=250, margin=(0, 3))

        self.read_data(IMAGE_URL, IMAGE_EXT, True)
        self.show_image(self.base_ds)

        # Link left side objects

        url_input.param.watch(self.process_input, 'value')
        self.file_input.param.watch(self.process_input, 'value')

        self.pixelate_group.param.watch(self.pixelate_update, 'value')
        self.pixelate_slider.param.watch(self.pixelate_update, 'value')

        self.text_input.param.watch(self.text_input_update, 'value')
        self.divider_toggle.param.watch(self.toggle_update, 'value')
        self.embed_toggle.param.watch(self.toggle_update, 'value')
        self.highlight_toggle.param.watch(self.toggle_update, 'value')

        remove_button.on_click(self.remove_update)
        undo_button.on_click(self.undo_update)
        clear_button.on_click(self.clear_update)

        # Create left side layout

        slider_row = pn.Row(
            self.pixelate_group, self.pixelate_slider,
            sizing_mode=STR_WIDTH, margin=(0, 6))
        self.color_row = pn.Row(
            self.make_color_row(C.CLRS['white_smoke']), margin=(0, 11, 10, 11),
            sizing_mode=STR_WIDTH)
        toggles_row = pn.Row(self.divider_toggle, self.embed_toggle,
                             self.highlight_toggle, sizing_mode=STR_WIDTH)
        buttons_col = pn.Column(remove_button, undo_button, clear_button)
        select_row = pn.Row(
            self.multi_select, buttons_col, sizing_mode=STR_WIDTH,
            margin=(0, 0, 10, 0))

        left_layout = pn.WidgetBox(
            url_input,
            self.file_input,
            self.image_pane,
            slider_row,
            self.text_input,
            self.color_row,
            toggles_row,
            select_row,
            sizing_mode=STR_BOTH
        )

        # Create right side widgets

        self.output_group = pn.widgets.RadioButtonGroup(
            options=[HEXCODE, RGB_255, RGB_1], margin=(15, 10, 5, 10))
        self.num_slider = pn.widgets.IntSlider(
            name='Number of colors', start=2, end=255, step=1, value=1,
            margin=(10, 15))
        data = np.load(C.PATHS['tmp'])[::-1]
        plot_da = xr.DataArray(data, name='tmp', dims=('y', 'x'))
        self.hv_plot = hv.Image(plot_da, ['x', 'y'], ['tmp']).opts(
            responsive=True, min_height=500, toolbar=None, colorbar=True,
            default_tools=[], cmap=DEFAULT_CMAP,
            colorbar_opts={'background_fill_color': C.CLRS['white_smoke']},
            xaxis=None, yaxis=None, hooks=[remove_white_borders], aspect='equal'
        )
        self.plot_pane = pn.pane.HoloViews(
            min_height=300, max_height=500, object=self.hv_plot,
            sizing_mode='scale_both', align='center', margin=(0, 3))
        self.code_markdown = pn.pane.Markdown(
            EXAMPLE_CODE.format(colors=''),
            sizing_mode=STR_WIDTH, margin=(0, 15, 0, 15))

        # Link right side objects

        self.output_group.param.watch(self.toggle_update, 'value')
        self.num_slider.param.watch(self.slider_update, 'value')

        # Create right side layout

        right_layout = pn.WidgetBox(
            self.output_group,
            self.num_slider,
            self.plot_pane,
            self.code_markdown,
            sizing_mode=STR_BOTH
        )

        # Create bottom side layout

        bottom_layout = pn.Row(
            left_layout,
            right_layout,
            sizing_mode=STR_WIDTH,
        )

        # Create dashboard

        layout = pn.Column(
            top_layout,
            bottom_layout,
            sizing_mode=STR_BOTH,
            margin=0
        )
        return layout
