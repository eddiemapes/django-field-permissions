from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

from field_permissions.models import FieldPermission


@admin.register(FieldPermission)
class FieldPermissionAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'field_name', 'access_level', 'display_name')
    list_filter = ('model_name', 'access_level')
    search_fields = ('model_name', 'field_name')
    filter_horizontal = ('users', 'groups')


class FieldPermissionUserAdminMixin:
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        field_perms_field = forms.ModelMultipleChoiceField(
            queryset=FieldPermission.objects.all(),
            required=False,
            widget=FilteredSelectMultiple('Field Permissions', is_stacked=False),
        )

        if obj:
            field_perms_field.initial = FieldPermission.objects.filter(users=obj)

        form.base_fields['field_permissions'] = field_perms_field
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = list(fieldsets) + [
            ('Field Permissions', {'fields': ('field_permissions',)}),
        ]
        return fieldsets

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        submitted = set(form.cleaned_data.get('field_permissions', []))
        current = set(FieldPermission.objects.filter(users=obj))

        for perm in submitted - current:
            perm.users.add(obj)

        for perm in current - submitted:
            perm.users.remove(obj)


class FieldPermissionGroupAdminMixin:
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        field_perms_field = forms.ModelMultipleChoiceField(
            queryset=FieldPermission.objects.all(),
            required=False,
            widget=FilteredSelectMultiple('Field Permissions', is_stacked=False),
        )

        if obj:
            field_perms_field.initial = FieldPermission.objects.filter(groups=obj)

        form.base_fields['field_permissions'] = field_perms_field
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = list(fieldsets) + [
            ('Field Permissions', {'fields': ('field_permissions',)}),
        ]
        return fieldsets

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        submitted = set(form.cleaned_data.get('field_permissions', []))
        current = set(FieldPermission.objects.filter(groups=obj))

        for perm in submitted - current:
            perm.groups.add(obj)

        for perm in current - submitted:
            perm.groups.remove(obj)
