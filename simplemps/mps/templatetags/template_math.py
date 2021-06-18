from django import template

register = template.Library()

@register.filter(name='mult')
def mult(value, arg):
    return value * arg

@register.filter(name='div')
def div(value, arg):
    return value / arg

@register.filter(name='bool_to_int')
def bool_to_int(value):
    return 1 if value else 0
