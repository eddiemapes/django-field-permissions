from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import User, Group


class FieldPermission(models.Model):
    model_name = models.CharField(max_length=200)
    field_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200, null=True, blank=True)
    access_level = models.CharField(
        max_length=50,
        choices=[
            ('read', 'Read Access'),
            ('edit', 'Edit Access'),
        ],
    )
    users = models.ManyToManyField(User, blank=True)
    groups = models.ManyToManyField(Group, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['model_name', 'field_name', 'access_level'],
                name='unique_model_field_access',
            ),
        ]
        verbose_name = 'Field Permission'
        verbose_name_plural = 'Field Permissions'

    def __str__(self):
        return f'{self.model_name}.{self.field_name} - {self.access_level}'
