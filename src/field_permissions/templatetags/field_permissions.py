from django import template

from field_permissions.permissions import has_field_perm

register = template.Library()


@register.filter(name='has_field_perm')
def has_field_perm_filter(request, arg):
    parts = arg.split(',')
    if len(parts) != 3:
        raise ValueError('Invalid parameters for field permissions template tag. Must be in format "model_name,field_name,access_level".')
    model_name = parts[0].strip()
    field_name = parts[1].strip()
    access_level = parts[2].strip()
    return has_field_perm(request, model_name, field_name, access_level)
