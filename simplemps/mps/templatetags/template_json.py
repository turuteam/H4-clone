from django import template
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder

import json

register = template.Library()

@register.filter(name='json')
def json_dumps(data):
    unsafe_chars = {
        '&': '\\u0026',
        '<': '\\u003c',
        '>': '\\u003e',
        '\u2028': '\\u2028',
        '\u2029': '\\u2029'}
    json_str = json.dumps(data, cls=DjangoJSONEncoder)

    for (c, d) in unsafe_chars.items():
        json_str = json_str.replace(c, d)

    return json_str