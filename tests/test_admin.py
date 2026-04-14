"""
Unit tests for FieldPermissionUserAdminMixin and FieldPermissionGroupAdminMixin.

We test the mixin methods directly by constructing a minimal concrete admin
class rather than spinning up a full HTTP admin client. This avoids the need
for django.contrib.admin / sessions / messages in INSTALLED_APPS.

MRO design:
  ConcreteUserAdmin(FieldPermissionUserAdminMixin, BaseUserAdmin)
  MRO: Concrete → Mixin → Base → object

This means `super()` calls inside the mixin land on BaseUserAdmin, which
provides the raw "upstream" behaviour the mixin is designed to augment.
"""

import pytest
from unittest.mock import MagicMock

from field_permissions.admin import FieldPermissionGroupAdminMixin, FieldPermissionUserAdminMixin
from field_permissions.models import FieldPermission


# ---------------------------------------------------------------------------
# Base classes (simulate upstream UserAdmin / GroupAdmin)
# ---------------------------------------------------------------------------

class BaseUserAdmin:
    def get_fields(self, request, obj=None):
        return ["username", "email", "field_permissions", "password"]

    def get_form(self, request, obj=None, **kwargs):
        form = MagicMock()
        form.base_fields = {}
        return form

    def get_fieldsets(self, request, obj=None):
        return [
            (None, {"fields": ("username", "field_permissions", "password")}),
            ("Personal info", {"fields": ("email",)}),
        ]

    def save_related(self, request, form, formsets, change):
        pass  # base does nothing


class BaseGroupAdmin:
    def get_fields(self, request, obj=None):
        return ["name", "field_permissions"]

    def get_form(self, request, obj=None, **kwargs):
        form = MagicMock()
        form.base_fields = {}
        return form

    def get_fieldsets(self, request, obj=None):
        return [
            (None, {"fields": ("name", "field_permissions")}),
        ]

    def save_related(self, request, form, formsets, change):
        pass


# ---------------------------------------------------------------------------
# Concrete classes (mixin sits first so its methods run, then super() → Base)
# ---------------------------------------------------------------------------

class ConcreteUserAdmin(FieldPermissionUserAdminMixin, BaseUserAdmin):
    pass


class ConcreteGroupAdmin(FieldPermissionGroupAdminMixin, BaseGroupAdmin):
    pass


# ---------------------------------------------------------------------------
# FieldPermissionUserAdminMixin — get_fields
# ---------------------------------------------------------------------------

def test_user_get_fields_removes_field_permissions():
    admin = ConcreteUserAdmin()
    fields = admin.get_fields(request=None)
    assert "field_permissions" not in fields
    assert "username" in fields
    assert "email" in fields


# ---------------------------------------------------------------------------
# FieldPermissionUserAdminMixin — get_fieldsets
# ---------------------------------------------------------------------------

def test_user_get_fieldsets_strips_field_permissions_from_existing():
    admin = ConcreteUserAdmin()
    fieldsets = admin.get_fieldsets(request=None)
    # The mixin appends a "Field Permissions" section that legitimately owns the
    # field_permissions field. Check that it was stripped from all upstream sections.
    for name, options in fieldsets:
        if name == "Field Permissions":
            continue
        assert "field_permissions" not in options.get("fields", ())


def test_user_get_fieldsets_appends_field_permissions_section():
    admin = ConcreteUserAdmin()
    fieldsets = admin.get_fieldsets(request=None)
    section_names = [name for name, _ in fieldsets]
    assert "Field Permissions" in section_names


def test_user_get_fieldsets_field_permissions_section_last():
    admin = ConcreteUserAdmin()
    fieldsets = admin.get_fieldsets(request=None)
    last_name, last_options = fieldsets[-1]
    assert last_name == "Field Permissions"
    assert "field_permissions" in last_options["fields"]


# ---------------------------------------------------------------------------
# FieldPermissionUserAdminMixin — save_related
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_user_save_related_adds_new_perm(user):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )

    form = MagicMock()
    form.instance = user
    form.cleaned_data = {"field_permissions": [perm]}

    admin = ConcreteUserAdmin()
    admin.save_related(request=None, form=form, formsets=[], change=True)

    assert perm.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_user_save_related_removes_deselected_perm(user):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.users.add(user)

    form = MagicMock()
    form.instance = user
    form.cleaned_data = {"field_permissions": []}  # de-selected

    admin = ConcreteUserAdmin()
    admin.save_related(request=None, form=form, formsets=[], change=True)

    assert not perm.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_user_save_related_keeps_unchanged_perm(user):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.users.add(user)

    form = MagicMock()
    form.instance = user
    form.cleaned_data = {"field_permissions": [perm]}  # still selected

    admin = ConcreteUserAdmin()
    admin.save_related(request=None, form=form, formsets=[], change=True)

    assert perm.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_user_save_related_handles_empty_submission(user):
    form = MagicMock()
    form.instance = user
    form.cleaned_data = {"field_permissions": []}

    admin = ConcreteUserAdmin()
    admin.save_related(request=None, form=form, formsets=[], change=False)
    # no exception


# ---------------------------------------------------------------------------
# FieldPermissionGroupAdminMixin — get_fields
# ---------------------------------------------------------------------------

def test_group_get_fields_removes_field_permissions():
    admin = ConcreteGroupAdmin()
    fields = admin.get_fields(request=None)
    assert "field_permissions" not in fields
    assert "name" in fields


# ---------------------------------------------------------------------------
# FieldPermissionGroupAdminMixin — get_fieldsets
# ---------------------------------------------------------------------------

def test_group_get_fieldsets_appends_section():
    admin = ConcreteGroupAdmin()
    fieldsets = admin.get_fieldsets(request=None)
    section_names = [name for name, _ in fieldsets]
    assert "Field Permissions" in section_names


def test_group_get_fieldsets_strips_existing_field_permissions():
    admin = ConcreteGroupAdmin()
    fieldsets = admin.get_fieldsets(request=None)
    for name, options in fieldsets:
        if name == "Field Permissions":
            continue
        assert "field_permissions" not in options.get("fields", ())


# ---------------------------------------------------------------------------
# FieldPermissionGroupAdminMixin — save_related
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_group_save_related_adds_new_perm(group):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )

    form = MagicMock()
    form.instance = group
    form.cleaned_data = {"field_permissions": [perm]}

    admin = ConcreteGroupAdmin()
    admin.save_related(request=None, form=form, formsets=[], change=True)

    assert perm.groups.filter(pk=group.pk).exists()


@pytest.mark.django_db
def test_group_save_related_removes_deselected_perm(group):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.groups.add(group)

    form = MagicMock()
    form.instance = group
    form.cleaned_data = {"field_permissions": []}

    admin = ConcreteGroupAdmin()
    admin.save_related(request=None, form=form, formsets=[], change=True)

    assert not perm.groups.filter(pk=group.pk).exists()
