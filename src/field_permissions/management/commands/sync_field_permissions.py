from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.db.models import ManyToOneRel

from field_permissions.models import FieldPermission


class Command(BaseCommand):
    help = 'Syncs field permission records for models listed in FIELD_PERMISSIONS_ALLOWED_MODELS'

    def handle(self, *args, **options):
        allowed_models = getattr(settings, 'FIELD_PERMISSIONS_ALLOWED_MODELS', [])

        if not allowed_models:
            self.stdout.write('No models configured in FIELD_PERMISSIONS_ALLOWED_MODELS.')
            return

        total_created = 0

        for model_path in allowed_models:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
            stored_name = model._meta.model_name

            model_fields = model._meta.get_fields()
            filtered_fields = [
                field for field in model_fields
                if not isinstance(field, ManyToOneRel)
            ]

            existing = set(
                FieldPermission.objects.filter(
                    model_name=stored_name
                ).values_list('field_name', 'access_level')
            )

            to_create = []
            for field in filtered_fields:
                for access_level in ['read', 'edit']:
                    if (field.name, access_level) not in existing:
                        display = getattr(field, 'verbose_name', field.name)
                        to_create.append(
                            FieldPermission(
                                model_name=stored_name,
                                field_name=field.name,
                                display_name=display,
                                access_level=access_level,
                            )
                        )

            if to_create:
                with transaction.atomic():
                    FieldPermission.objects.bulk_create(to_create)
                total_created += len(to_create)
                self.stdout.write(f'Created {len(to_create)} permissions for {model_path}.')
            else:
                self.stdout.write(f'No new permissions needed for {model_path}.')

        self.stdout.write(f'Sync complete. {total_created} total permissions created.')
