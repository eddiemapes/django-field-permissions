from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

from field_permissions.models import FieldPermission


class FieldPermissionUserAdminMixin:
    def get_fields(self, request, obj=None):
        return [f for f in super().get_fields(request, obj) if f != 'field_permissions']

    def get_form(self, request, obj=None, **kwargs):
        fields = kwargs.get('fields')
        if fields is not None:
            kwargs['fields'] = [f for f in fields if f != 'field_permissions']
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
        cleaned = [
            (name, {**options, 'fields': tuple(f for f in options.get('fields', ()) if f != 'field_permissions')})
            for name, options in fieldsets
        ]
        return cleaned + [('Field Permissions', {'fields': ('field_permissions',)})]

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
    def get_fields(self, request, obj=None):
        return [f for f in super().get_fields(request, obj) if f != 'field_permissions']

    def get_form(self, request, obj=None, **kwargs):
        fields = kwargs.get('fields')
        if fields is not None:
            kwargs['fields'] = [f for f in fields if f != 'field_permissions']
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
        cleaned = [
            (name, {**options, 'fields': tuple(f for f in options.get('fields', ()) if f != 'field_permissions')})
            for name, options in fieldsets
        ]
        return cleaned + [('Field Permissions', {'fields': ('field_permissions',)})]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        submitted = set(form.cleaned_data.get('field_permissions', []))
        current = set(FieldPermission.objects.filter(groups=obj))

        for perm in submitted - current:
            perm.groups.add(obj)

        for perm in current - submitted:
            perm.groups.remove(obj)
