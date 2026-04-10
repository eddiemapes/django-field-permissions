# django-field-permissions

Django's built-in permission system works at the model level — a user can either access a model or they can't. There's isn't a built-in way to say "this user can see the `email` field but not edit it." **django-field-permissions** fills that gap by adding field-level `read` and `edit` permissions that can be assigned to individual users or groups.

[![PyPI version](https://img.shields.io/pypi/v/django-field-permissions)](https://pypi.org/project/django-field-permissions/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Overview

django-field-permissions introduces a `FieldPermission` model that maps a model field to an access level (`read` or `edit`) and a set of users and/or groups. A middleware resolves the current user's permissions on every request and attaches them to `request.field_perms`. A template tag and a utility function let you check those permissions anywhere in your templates or views.

**Key features:**

- Per-field `read` and `edit` access levels
- Assign permissions to individual users, groups, or both
- Check a user's field permissions in the template or backend
- Superusers automatically pass all permission checks
- Middleware-driven — resolved permissions are available on every request via `request.field_perms`
- Built-in caching with automatic invalidation via Django signals
- Django admin integration for managing permissions through the UI

---

## Installation

```bash
pip install django-field-permissions
```

---

## Quick Start

**1. Add to `INSTALLED_APPS`:**

```python
INSTALLED_APPS = [
    ...
    'field_permissions',
]
```

**2. Add the middleware:**

```python
MIDDLEWARE = [
    ...
    'field_permissions.middleware.FieldPermissionMiddleware',
]
```
Place this after AuthenticationMiddleware.

**3. Declare which models get field permissions:**

```python
# settings.py
FIELD_PERMISSIONS_ALLOWED_MODELS = [
    'myapp.MyModel',
    'otherapp.AnotherModel',
]
```

**4. Run migrations and sync permissions:**

```bash
python manage.py migrate
python manage.py sync_field_permissions
```

This creates one `read` record and one `edit` record in the database for every field on every model listed in `FIELD_PERMISSIONS_ALLOWED_MODELS`.


**5. Assign permissions in the Django admin:**

**Optional — wire up admin mixins to manage permissions from the User or Group admin pages:**

```python
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from field_permissions.admin import FieldPermissionUserAdminMixin, FieldPermissionGroupAdminMixin

class MyUserAdmin(FieldPermissionUserAdminMixin, UserAdmin):
    pass

class MyGroupAdmin(FieldPermissionGroupAdminMixin, GroupAdmin):
    pass

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, MyUserAdmin)
admin.site.register(Group, MyGroupAdmin)
```

---

Go to **Field Permissions** in the admin and add users or groups to the appropriate records. 

Otherwise permission records can be created via SQL / Django Shell.


**6. Check permissions in templates:**

```django
{% load field_permissions %}

{% if request|has_field_perm:"mymodel,email,read" %}
    {{ user.email }}
{% endif %}
```


**7. Check permissions in views:**

```python
from field_permissions.permissions import has_field_perm

def my_view(request):
    if has_field_perm(request, 'mymodel', 'email', 'edit'):
        # allow edit
        pass
```


## Configuration

All settings are optional. Add any of the following to your `settings.py`:

| Setting | Default | Description |
|---|---|---|
| `FIELD_PERMISSIONS_ALLOWED_MODELS` | `[]` | Models to create field permissions for. Format: `["appname.ModelName"]` |
| `FIELD_PERMISSIONS_ENABLE` | `True` | Enable or disable the middleware globally |
| `FIELD_PERMISSIONS_USE_CACHE` | `True` | Cache resolved permissions per user |
| `FIELD_PERMISSIONS_CACHE_TIMEOUT` | `3600` | Cache TTL in seconds (default: 1 hour) |

Caches are automatically invalidated when any `FieldPermission` record or its user/group assignments change.

---

## License

MIT — see [LICENSE](LICENSE) for details.
