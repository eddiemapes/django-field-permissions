import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models import ManyToOneRel
from django.test import override_settings

from field_permissions.models import FieldPermission


# ---------------------------------------------------------------------------
# Empty configuration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_empty_allowed_models_creates_nothing(capsys):
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=[]):
        call_command("sync_field_permissions")

    assert FieldPermission.objects.count() == 0
    captured = capsys.readouterr()
    assert "No models configured" in captured.out


# ---------------------------------------------------------------------------
# Record creation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_creates_read_and_edit_for_each_field():
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")

    filtered_fields = [
        f for f in User._meta.get_fields()
        if not isinstance(f, ManyToOneRel)
    ]
    expected_count = len(filtered_fields) * 2  # read + edit per field
    assert FieldPermission.objects.filter(model_name="user").count() == expected_count


@pytest.mark.django_db
def test_excludes_many_to_one_rel_fields():
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")

    # ManyToOneRel fields would have names like "logentry" (reverse FK).
    # Collect which field names were created.
    created_field_names = set(
        FieldPermission.objects.filter(model_name="user").values_list(
            "field_name", flat=True
        )
    )

    reverse_rel_names = {
        f.name for f in User._meta.get_fields() if isinstance(f, ManyToOneRel)
    }
    # None of the reverse-relation names should appear in created records
    assert created_field_names.isdisjoint(reverse_rel_names)


@pytest.mark.django_db
def test_both_access_levels_created_per_field():
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")

    email_read = FieldPermission.objects.filter(
        model_name="user", field_name="email", access_level="read"
    ).exists()
    email_edit = FieldPermission.objects.filter(
        model_name="user", field_name="email", access_level="edit"
    ).exists()
    assert email_read
    assert email_edit


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_running_twice_creates_no_duplicates():
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")
        count_first = FieldPermission.objects.count()
        call_command("sync_field_permissions")
        count_second = FieldPermission.objects.count()

    assert count_first == count_second


@pytest.mark.django_db
def test_second_run_reports_no_new_permissions_needed(capsys):
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")
        capsys.readouterr()  # discard first run output
        call_command("sync_field_permissions")

    captured = capsys.readouterr()
    assert "No new permissions needed" in captured.out


# ---------------------------------------------------------------------------
# display_name population
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_display_name_set_from_verbose_name():
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")

    perm = FieldPermission.objects.get(
        model_name="user", field_name="email", access_level="read"
    )
    # django.contrib.auth.models.User.email has verbose_name "email address"
    assert perm.display_name == "email address"


@pytest.mark.django_db
def test_display_name_falls_back_to_field_name():
    """Fields without verbose_name (e.g. M2M through fields) use field.name."""
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")

    # Verify that all created records have a non-empty display_name
    empty_display = FieldPermission.objects.filter(
        model_name="user", display_name=""
    ).count()
    assert empty_display == 0


# ---------------------------------------------------------------------------
# model_name stored as _meta.model_name (lowercase)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_model_name_stored_as_meta_model_name():
    with override_settings(FIELD_PERMISSIONS_ALLOWED_MODELS=["auth.User"]):
        call_command("sync_field_permissions")

    # _meta.model_name for User is "user"
    assert FieldPermission.objects.filter(model_name="user").exists()
    assert not FieldPermission.objects.filter(model_name="User").exists()
