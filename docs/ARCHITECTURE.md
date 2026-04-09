### How Permission Records are Created
- sync_field_permissions.py handles creation via a management command
- Calls model._meta.get_fields() to discover all fields on each model in the ALLOWED_MODELS variable set in settings.py
- For each field, it creates two FieldPermission records (one read, one edit) if they don't already exist
- Uses bulk_create() for efficiency


### How Permissions are Assigned to Users/Groups
- Django admin integration allows admin users to assign field-level permissions to users and groups
- Superusers by default have read and edit access on every field. 
- Superuser override logic will occur in the environment processor.


### How Permissions Are Made Available Application-Wide
Context processor — environment_variable() is registered in settings and runs on every request. For authenticated users, it calls get_users_field_level_permissions(user) and adds the result as field_perms to the template context.

- Template tag — has_field_perm is a filter that checks membership in the set:

```
    {% load field_permissions %}

    {% if field_perms|has_field_perm:"claim,Analyst_ID,read" %}
    <!-- user can see this field -->
    {% endif %}

    {% if field_perms|has_field_perm:"claim,Claim_name,edit" %}
    <!-- user can edit this field -->
    {% endif %}
```