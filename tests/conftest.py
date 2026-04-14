import pytest
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import RequestFactory

from field_permissions.models import FieldPermission


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass")


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username="admin", password="pass")


@pytest.fixture
def group(db):
    return Group.objects.create(name="testgroup")


@pytest.fixture
def field_perm(db):
    return FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )


@pytest.fixture
def authed_request(rf, user):
    request = rf.get("/")
    request.user = user
    return request
