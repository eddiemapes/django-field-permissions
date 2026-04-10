### How Field Permission Records are Created
- sync_field_permissions.py handles creation via a management command
- Calls model._meta.get_fields() to discover all fields on each model in the ALLOWED_MODELS variable set in settings.py
- For each field, two FieldPermission records are created (read, edit) if they don't already exist
- Uses bulk_create() for efficiency


### How Field Permissions are Assigned to Users/Groups
- Django admin integration allows admin users to assign field-level permissions to users and groups
- Superusers by default have read and edit access on every field
- Superuser override logic will occur in the has_field_perm() function


### How Field Permissions are Made Available Application-Wide
- Permissions are attached to the request via middleware
- This way the user's field permissions are available for backend and frontend validation via the request object


### How Field Permissions are Checked in the Template
- A template filter is used that is loaded in with {% load field_permissions %}
- The syntax for checking field permissions in templates is as follows: {% if request|has_field_perm:"model,field,access_level" %}
- For example:
```
    {% if request|has_field_perm:"user,email,read" %}
        {{ user.email }}
    {% endif %}
```
- The code in the template filter will call the has_field_perm() function in permissions.py
- The permission check in the template layer is primarily for controlling visibility in the UI

### How Field Permissions are Checked in the View
- A helper function called has_field_perm() is available to import in field_permissions.permissions
- This function takes in request, model_name, field_name, access_level and returns True/False
- Superuser override takes place here