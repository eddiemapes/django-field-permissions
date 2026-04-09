## Package Overview
This section describes how the package works on each level.

### The Model
FieldPermission in models.py stores permission records. Each record represents a single model + field + access level combination:

- model_name / field_name — string references to the target (e.g. "first_name", "address")
- access_level — either 'read' or 'edit'
- users — ManyToMany to User
- groups — ManyToMany to Group
- UniqueConstraint on (model_name, field_name, access_level) — so there's one "read" record and one "edit" record per field

Exclude the created_by and modified_by fields in the reference model.

### Caching
- Field-level permission records are cached in environment_processor.py:
- Cache key: 'user_field_perms_{user_id}' (specific to each user)
- Timeout: Default to 3600 seconds (1 hour), updatable through the FIELD_PERMISSIONS_CACHE_TIMEOUT variable in settings.py
- Backend: Redis in dev/prod, LocMemCache locally
- Cached value: a set of tuples like {('claim', 'Analyst_ID', 'read'), ...}

### Template Tag
The template tag accesses the user's field_permissions using the context variable made available through the context processor.

- File within templatetags directory: field_permission_filter.py
- Function within file: has_field_perm()
- This function takes in model_name, field_name, and access_level from the template filter and uses this combination to check whether or not the user has the required access

### Settings Variables
These settings can be set in the package user's settings.py file. Each come with a reasonable default value in the event they aren't set

- FIELD_PERMISSIONS_CACHE_TIMEOUT - How long the user's field permissions should be cached. Default to 3600 seconds (1 hour)
- FIELD_PERMISSIONS_ALLOWED_MODELS - Which of the user's models should have field-permission records created. Default to an empty list