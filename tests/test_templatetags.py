import pytest
from django.template import Context, Template
from django.test import RequestFactory

from field_permissions.templatetags.field_permissions import has_field_perm_filter


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def test_too_few_parts_raises_value_error(authed_request):
    with pytest.raises(ValueError, match="Invalid parameters"):
        has_field_perm_filter(authed_request, "user,email")


def test_too_many_parts_raises_value_error(authed_request):
    with pytest.raises(ValueError, match="Invalid parameters"):
        has_field_perm_filter(authed_request, "user,email,read,extra")


def test_empty_string_raises_value_error(authed_request):
    with pytest.raises(ValueError):
        has_field_perm_filter(authed_request, "")


# ---------------------------------------------------------------------------
# Delegation to has_field_perm
# ---------------------------------------------------------------------------

def test_valid_arg_delegates_correctly(mocker, authed_request):
    mock_perm = mocker.patch(
        "field_permissions.templatetags.field_permissions.has_field_perm",
        return_value=True,
    )
    result = has_field_perm_filter(authed_request, "user,email,read")

    mock_perm.assert_called_once_with(authed_request, "user", "email", "read")
    assert result is True


def test_whitespace_in_arg_is_stripped(mocker, authed_request):
    mock_perm = mocker.patch(
        "field_permissions.templatetags.field_permissions.has_field_perm",
        return_value=False,
    )
    has_field_perm_filter(authed_request, " user , email , read ")
    mock_perm.assert_called_once_with(authed_request, "user", "email", "read")


# ---------------------------------------------------------------------------
# Full template rendering
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_template_renders_truthy_branch(rf, user):
    request = rf.get("/")
    request.user = user
    request.field_perms = {("user", "email", "read")}

    tmpl = Template(
        "{% load field_permissions %}"
        "{% if request|has_field_perm:'user,email,read' %}yes{% endif %}"
    )
    output = tmpl.render(Context({"request": request}))
    assert output == "yes"


@pytest.mark.django_db
def test_template_renders_falsy_branch(rf, user):
    request = rf.get("/")
    request.user = user
    request.field_perms = set()

    tmpl = Template(
        "{% load field_permissions %}"
        "{% if request|has_field_perm:'user,email,read' %}yes{% else %}no{% endif %}"
    )
    output = tmpl.render(Context({"request": request}))
    assert output == "no"
