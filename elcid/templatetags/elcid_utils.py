from django import template
register = template.Library()


@register.filter
def month(input):
    """
    Takes an integer returns a month
    """
    if input == 1:
        return "Jan"

    if input == 2:
        return "Feb"

    if input == 3:
        return "Mar"

    if input == 4:
        return "Apr"

    if input == 5:
        return "May"

    if input == 6:
        return "Jun"

    if input == 7:
        return "Jul"

    if input == 8:
        return "Aug"

    if input == 9:
        return "Sep"

    if input == 10:
        return "Oct"

    if input == 11:
        return "Nov"

    if input == 12:
        return "Dec"

    return ""

