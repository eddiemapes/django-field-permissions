from typing import Literal
from django.http import HttpRequest
from django.apps import apps
from django.db.models import Model

AccessLevel = Literal['read', 'edit']

def has_field_perm(request: HttpRequest, model_name: str, field_name: str, access_level: AccessLevel) -> bool:
    # Verify access_level
    if access_level not in ['read', 'edit']:
        raise ValueError(f'Invalid field permission access level "{access_level}". Must be "read" or "edit".')

    # Verify model_name 
    if not isinstance(model_name, str):
        raise TypeError(f'model_name must be of type str, received type {type(model_name)}')

    # Verify field_name 
    if not isinstance(field_name, str):
        raise TypeError(f'field_name must be of type str, received type {type(field_name)}')

    # Superuser override check 
    if request.user.is_superuser:
        return True

    # If field permissions are not attached via middleware, return False 
    if not hasattr(request, 'field_perms'):
        return False

    # Clean parameters
    model_name_cleaned = model_name.lower()
    field_name_cleaned = field_name.lower()
    access_level_cleaned = access_level.lower()

    # Verify the model is included in apps 
    if not check_model_in_project(model_name_cleaned):
        raise LookupError(f'Model named {model_name} not found in the app registry.')

    # Verify the field exists on the model 
    if not check_field_in_model(model_name_cleaned, field_name_cleaned):
        raise LookupError(f'Field named {field_name} not found on model {model_name}')

    # Return True/False if user has field-level permission 
    return (model_name_cleaned, field_name_cleaned, access_level_cleaned) in request.field_perms


def check_model_in_project(model_name: str) -> bool:
    return model_name in [model.__name__.lower() for model in apps.get_models()]


def check_field_in_model(model_name: str, field_name: str) -> bool:
    model: Model = get_model_from_str(model_name)
    return field_name in [field.name.lower() for field in model._meta.get_fields()]


def get_model_from_str(model_name: str) -> Model:
    for app_config in apps.get_app_configs():
        try:
            return app_config.get_model(model_name)
        except LookupError:
            continue
    raise LookupError(f'Model named {model_name} not found in the app registry.')

