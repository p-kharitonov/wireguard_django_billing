import base64

from django import template

register = template.Library()


@register.filter
def base64encode(string: str) -> str:
    return base64.b64encode(string.encode('utf-8')).decode('ascii')
