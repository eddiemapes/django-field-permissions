## Package Overview
This section describes how the package works on each level.

### Model Schema
FieldPermission in models.py stores permission records. Each record represents a single model + field + access level combination:

- model_name - string references to the model name
- field_name — string references to the field (e.g. "first_name", "address")
- display_name - string reference to the field's verbose name attribute
- access_level — either 'read' or 'edit'
- users — ManyToMany to User
- groups — ManyToMany to Group
- UniqueConstraint on (model_name, field_name, access_level) — so there's one "read" record and one "edit" record per field

Exclude the created_by and modified_by fields in the reference model.

### Middleware
- Called field_permission.middleware.FieldPermissionMiddleware
- Comes after any request middleware so that the request object is available
- Responsible for checking for the user's field-level permissions into a set object and appending to the request object
- Middleware caches field permissions if FIELD_PERMISSIONS_USE_CACHE is enabled in settings
- Check for FIELD_PERMISSIONS_ENABLE setting True. If not, exit early
- Check for an authenticated user. If not, exit early

### Caching
- Field-level permission records are cached in the middleware if the FIELD_PERMISSIONS_USE_CACHE is enabled
- Cache key: 'user_field_perms_{user_id}' (specific to each user)
- Timeout: Default to 3600 seconds (1 hour), updatable through the FIELD_PERMISSIONS_CACHE_TIMEOUT variable in settings.py
- Backend: Redis in dev/prod, LocMemCache locally
- Cached value: a set of tuples like {('claim', 'Analyst_ID', 'read'), ...}

### Cache Invalidation - Signals.py
- Signals in signals.py will listen for M2M changes on the user and group junction tables and changes to the FieldPermission table
- If any changes occur in any of these tables the cache will be invalidated

### Template Tag
The template tag accesses the user's field_permissions using the context variable made available through the context processor.

- File within templatetags directory: field_permissions.py
- Function within file: has_field_perm()
- This function takes in model_name, field_name, and access_level from the template filter and uses this combination to check whether or not the user has the required access

### Settings Variables
These settings can be set in the package user's settings.py file. Each come with a reasonable default value in the event they aren't set

- FIELD_PERMISSIONS_ENABLE - Enables/disables the middleware from querying user/group field-permissions. Default to True
- FIELD_PERMISSIONS_USE_CACHE - Enables caching on field-permissions. Default to True
- FIELD_PERMISSIONS_CACHE_TIMEOUT - How long the user's field permissions should be cached. Default to 3600 seconds (1 hour)
- FIELD_PERMISSIONS_ALLOWED_MODELS - Which of the user's models should have field-permission records created. Expected format: ["appname.modelname"]. Default to an empty list

### Admin Integration
- Provide two mixins for the consumer to wire up in admin.py
- These will be FieldPermissionUserAdminMixin and FieldPermissionGroupAdminMixin available in field_permissions.admin
- These mixins will override get_form() and inject a ModelMultipleChoiceField with FilteredSelectMultiple widget. Queryset of all FieldPermission objects. Pre-select permissions already assigned to that user/group
- Override save_model() or save_related() to sync the M2M based on what was submitted
- Adds field to fieldsets or readonly_fields as appropriate
- Example implementation for the consumer:
```
# In the consumer's admin.py
from field_permissions.admin import FieldPermissionUserAdminMixin

class MyUserAdmin(FieldPermissionUserAdminMixin, UserAdmin):
    pass

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
```