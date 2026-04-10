from django.apps import AppConfig


class FieldPermissionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "field_permissions"
    verbose_name = "Field Permissions"

    def ready(self):
        import field_permissions.signals
