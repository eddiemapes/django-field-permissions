import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from field_permissions.middleware import FieldPermissionMiddleware
from field_permissions.models import FieldPermission


def get_response(request):
    return HttpResponse()


def build_middleware():
    return FieldPermissionMiddleware(get_response)


def make_request(rf, user):
    request = rf.get("/")
    request.user = user
    return request


# ---------------------------------------------------------------------------
# FIELD_PERMISSIONS_ENABLE = False
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_disabled_setting_skips_middleware(rf, user):
    middleware = build_middleware()
    request = make_request(rf, user)
    with override_settings(FIELD_PERMISSIONS_ENABLE=False):
        middleware(request)
    assert not hasattr(request, "field_perms")


# ---------------------------------------------------------------------------
# Unauthenticated user
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anonymous_user_no_field_perms(rf):
    middleware = build_middleware()
    request = rf.get("/")
    request.user = AnonymousUser()
    middleware(request)
    assert not hasattr(request, "field_perms")


@pytest.mark.django_db
def test_no_user_attr_no_field_perms(rf):
    middleware = build_middleware()
    request = rf.get("/")
    # no user attr at all
    middleware(request)
    assert not hasattr(request, "field_perms")


# ---------------------------------------------------------------------------
# Authenticated user — permission loading
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_authenticated_no_perms_gives_empty_set(rf, user):
    middleware = build_middleware()
    request = make_request(rf, user)
    middleware(request)
    assert hasattr(request, "field_perms")
    assert request.field_perms == set()


@pytest.mark.django_db
def test_direct_user_permission_appears(rf, user):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.users.add(user)

    middleware = build_middleware()
    request = make_request(rf, user)
    middleware(request)

    assert ("user", "email", "read") in request.field_perms


@pytest.mark.django_db
def test_group_permission_appears(rf, user, group):
    user.groups.add(group)
    perm = FieldPermission.objects.create(
        model_name="user", field_name="username", access_level="edit"
    )
    perm.groups.add(group)

    middleware = build_middleware()
    request = make_request(rf, user)
    middleware(request)

    assert ("user", "username", "edit") in request.field_perms


@pytest.mark.django_db
def test_user_and_group_same_perm_no_duplicate(rf, user, group):
    user.groups.add(group)
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.users.add(user)
    perm.groups.add(group)

    middleware = build_middleware()
    request = make_request(rf, user)
    middleware(request)

    # set semantics — only one occurrence
    matching = [p for p in request.field_perms if p == ("user", "email", "read")]
    assert len(matching) == 1


@pytest.mark.django_db
def test_multiple_permissions_all_loaded(rf, user):
    p1 = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    p2 = FieldPermission.objects.create(
        model_name="user", field_name="username", access_level="edit"
    )
    p1.users.add(user)
    p2.users.add(user)

    middleware = build_middleware()
    request = make_request(rf, user)
    middleware(request)

    assert ("user", "email", "read") in request.field_perms
    assert ("user", "username", "edit") in request.field_perms


# ---------------------------------------------------------------------------
# Caching behaviour
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cache_is_set_after_first_request(rf, user):
    middleware = build_middleware()
    request = make_request(rf, user)
    middleware(request)

    cached = cache.get(f"user_field_perms_{user.id}")
    assert cached is not None
    assert isinstance(cached, set)


@pytest.mark.django_db
def test_cache_hit_is_used_on_second_request(rf, user, django_assert_num_queries):
    middleware = build_middleware()

    # first request — populates cache
    middleware(make_request(rf, user))

    # second request — should hit cache, zero DB queries
    request2 = make_request(rf, user)
    with django_assert_num_queries(0):
        middleware(request2)

    assert hasattr(request2, "field_perms")


@pytest.mark.django_db
def test_cache_disabled_no_cache_written(rf, user):
    middleware = build_middleware()
    request = make_request(rf, user)
    with override_settings(FIELD_PERMISSIONS_USE_CACHE=False):
        middleware(request)

    assert cache.get(f"user_field_perms_{user.id}") is None


@pytest.mark.django_db
def test_cache_disabled_queries_db_every_request(rf, user, django_assert_num_queries):
    middleware = build_middleware()

    with override_settings(FIELD_PERMISSIONS_USE_CACHE=False):
        middleware(make_request(rf, user))
        # second call must still hit the DB (user.groups subquery + FieldPermission = 1 SQL)
        request2 = make_request(rf, user)
        with django_assert_num_queries(1):
            middleware(request2)


@pytest.mark.django_db
def test_cached_perms_attached_to_request(rf, user):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.users.add(user)

    middleware = build_middleware()
    # prime cache
    middleware(make_request(rf, user))

    # second request reads from cache — perms must still be present
    request2 = make_request(rf, user)
    middleware(request2)
    assert ("user", "email", "read") in request2.field_perms
