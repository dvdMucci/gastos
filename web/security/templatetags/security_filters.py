from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replace occurrences of 'old' with 'new' in the value.
    arg should be 'old,new'
    """
    old, new = arg.split(',', 1)
    return value.replace(old, new)