from django import template

register = template.Library()

@register.filter
def get_item(d, key):
    """Obtiene d[key] si existe."""
    try:
        return d.get(key)
    except Exception:
        return None

@register.filter
def get_attr(obj, attr_name):
    """Obtiene getattr(obj, attr_name) si existe."""
    try:
        if obj is None or not attr_name:
            return None
        return getattr(obj, attr_name, None)
    except Exception:
        return None
