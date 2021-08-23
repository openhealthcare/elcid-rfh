import json
from django import template

register = template.Library()


COLORS = [
    "#4676c5",
    "#d01c17",
    "#2e993e",
    "#e18400",
    "#3a8a8a",
    "#785713",
    "#75AAFF",
    "#C4B233",
    "#3DB8C4",
    "#C4685A",
    "#1F4178",
    "#9FC433",
]


@register.inclusion_tag(
    'tb/stats/templatetags/category_bar_chart.html'
)
def category_bar_chart(
    title, x_axis, field_vals, subtitle=False
):
    """
    Takes in a title, the x_axis, then a list of the
    other values with the first value being the name
    of the name of the row.

    Essentially the same as the c3 api.
    """
    colors = {}
    for idx, field_val in enumerate(field_vals):
        colors[field_val[0]] = COLORS[idx]
    ctx = {
        "table": {
            "x_axis": x_axis,
            "field_vals": field_vals,
        },
        "graph": {
            "x_axis": json.dumps(x_axis),
            "field_vals": json.dumps(field_vals),
            "colors": json.dumps(colors)
        },
        "title": title,
        "html_id": title.lower().replace(" ", "_").replace("/", ""),
        "subtitle": subtitle
    }
    return ctx


@register.filter
def color(idx):
    return COLORS[idx]


@register.inclusion_tag(
    'tb/stats/templatetags/value_display.html'
)
def value_display(value):
    if value is None:
        value = ""
    is_bool = False
    is_list = False

    if isinstance(value, list):
        is_list = True

    if isinstance(value, bool):
        is_bool = True

    return {
        "value": value,
        "is_bool": is_bool,
        "is_list": is_list
    }


@register.inclusion_tag(
    "tb/stats/templatetags/table_with_percent.html"
)
def table_with_percent(title, results):
    """
    Takes in the title, but also a dictionary
    of key to integer.
    """
    ctx = {"title": title, "table": {}}
    if not results:
        return ctx

    total = sum(results.values())
    for k, v in results.items():
        ctx["table"][k] = {
            "val": v,
            "percent": round(v/total * 100)
        }
    return ctx


@register.inclusion_tag(
    "tb/stats/templatetags/three_col_table_with_percent.html"
)
def three_col_table_with_percent(title, results):
    """
    Like table with percent but displays it in three colums
    """
    total = sum(results.values())
    tables = [{}, {}, {}]
    for idx, k in enumerate(results.keys()):
        tables[idx % 3][k] = {
            "val": results[k],
            "percent": round(results[k]/total * 100)
        }
    ctx = {
        "title": title,
        "tables": tables
    }
    return ctx


@register.inclusion_tag(
    "tb/stats/templatetags/pie_chart.html"
)
def pie_chart(
    title, field_vals
):
    """
    Takes in a title then a list of lists
    where the first item is the name of the pie
    chart like the c3 api.
    """
    field_vals = list(field_vals)
    colors = {}
    for idx, field_val in enumerate(field_vals):
        colors[field_val[0]] = COLORS[idx]
    return {
        "html_id": title.lower().replace(" ", "_"),
        "graph": {
            "field_vals": json.dumps(field_vals),
            "colors": json.dumps(colors)
        },
        "table": {
            "field_vals": dict(field_vals),
            "colors": json.dumps(colors)
        },
        "title": title,
    }
