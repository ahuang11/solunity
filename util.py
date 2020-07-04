import constant as C

def remove_white_borders(plot, element):
    p = plot.state
    p.border_fill_color = C.CLRS['white_smoke']
