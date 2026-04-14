import pytest
from django.test import RequestFactory

from field_permissions.permissions import (
    check_field_in_model,
    check_model_in_project,
    get_model_from_str,
    has_field_perm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(rf, user, field_perms=None):
    request = rf.get("/")
    request.user = user
    if field_perms is not None:
        request.field_perms = field_perms
    return request


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_invalid_access_level_raises_value_error(rf, user):
    request = make_request(rf, user, field_perms=set())
    with pytest.raises(ValueError, match="Invalid field permission access level"):
        has_field_perm(request, "user", "email", "write")


def test_invalid_access_level_empty_string(rf, user):
    request = make_request(rf, user, field_perms=set())
    with pytest.raises(ValueError):
        has_field_perm(request, "user", "email", "")


def test_non_string_model_name_raises_type_error(rf, user):
    request = make_request(rf, user, field_perms=set())
    with pytest.raises(TypeError, match="model_name must be of type str"):
        has_field_perm(request, 123, "email", "read")


def test_non_string_field_name_raises_type_error(rf, user):
    request = make_request(rf, user, field_perms=set())
    with pytest.raises(TypeError, match="field_name must be of type str"):
        has_field_perm(request, "user", None, "read")


# ---------------------------------------------------------------------------
# Superuser bypass
# ---------------------------------------------------------------------------

def test_superuser_returns_true_without_field_perms(rf, superuser):
    # No field_perms attr at all — superuser must still return True
    request = rf.get("/")
    request.user = superuser
    assert has_field_perm(request, "user", "email", "read") is True


def test_superuser_returns_true_regardless_of_field_perms(rf, superuser):
    request = make_request(rf, superuser, field_perms=set())
    assert has_field_perm(request, "user", "email", "read") is True


# ---------------------------------------------------------------------------
# Missing middleware
# ---------------------------------------------------------------------------

def test_no_field_perms_attr_returns_false(rf, user):
    request = make_request(rf, user)  # no field_perms set
    assert has_field_perm(request, "user", "email", "read") is False


# ---------------------------------------------------------------------------
# Model / field validation (LookupError)
# ---------------------------------------------------------------------------

def test_unknown_model_raises_lookup_error(rf, user):
    request = make_request(rf, user, field_perms=set())
    with pytest.raises(LookupError, match="not found in the app registry"):
        has_field_perm(request, "doesnotexist", "email", "read")


def test_unknown_field_raises_lookup_error(rf, user):
    request = make_request(rf, user, field_perms=set())
    with pytest.raises(LookupError, match="not found on model"):
        has_field_perm(request, "user", "nonexistent_field", "read")


# ---------------------------------------------------------------------------
# Case normalization
# ---------------------------------------------------------------------------

def test_uppercase_model_and_field_normalized(rf, user):
    # model_name and field_name are lowercased before the set lookup.
    # access_level is validated before normalization, so it must be lowercase.
    request = make_request(rf, user, field_perms={("user", "email", "read")})
    assert has_field_perm(request, "User", "Email", "read") is True


def test_uppercase_model_and_field_miss_after_normalization(rf, user):
    request = make_request(rf, user, field_perms=set())
    assert has_field_perm(request, "User", "Email", "read") is False


# ---------------------------------------------------------------------------
# Permission hit / miss
# ---------------------------------------------------------------------------

def test_perm_in_set_returns_true(rf, user):
    request = make_request(rf, user, field_perms={("user", "email", "read")})
    assert has_field_perm(request, "user", "email", "read") is True


def test_perm_not_in_set_returns_false(rf, user):
    request = make_request(rf, user, field_perms=set())
    assert has_field_perm(request, "user", "email", "read") is False


def test_read_does_not_grant_edit(rf, user):
    request = make_request(rf, user, field_perms={("user", "email", "read")})
    assert has_field_perm(request, "user", "email", "edit") is False


def test_edit_does_not_grant_read(rf, user):
    request = make_request(rf, user, field_perms={("user", "email", "edit")})
    assert has_field_perm(request, "user", "email", "read") is False


def test_different_field_is_independent(rf, user):
    request = make_request(rf, user, field_perms={("user", "email", "read")})
    assert has_field_perm(request, "user", "username", "read") is False


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def test_check_model_in_project_known():
    assert check_model_in_project("user") is True


def test_check_model_in_project_unknown():
    # Returns False (not raises) — LookupError is raised by has_field_perm
    assert check_model_in_project("totallyfakemodel") is False


def test_check_field_in_model_known():
    assert check_field_in_model("user", "email") is True


def test_check_field_in_model_unknown():
    # Returns False (not raises) — LookupError is raised by has_field_perm
    assert check_field_in_model("user", "notafield") is False


def test_get_model_from_str_returns_model_class():
    from django.contrib.auth.models import User
    assert get_model_from_str("user") is User


def test_get_model_from_str_unknown_raises():
    with pytest.raises(LookupError):
        get_model_from_str("completelyunknownmodel")
