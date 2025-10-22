from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Filtro personalizado para hacer lookup en diccionarios desde templates
    Uso: {{ diccionario|lookup:clave }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, [])

@register.filter
def get_item(dictionary, key):
    """
    Filtro alternativo para obtener items de diccionarios
    """
    return dictionary.get(key)

@register.simple_tag
def define(val=None):
    """
    Tag para definir variables en templates
    Uso: {% define "valor" as variable %}
    """
    return val
