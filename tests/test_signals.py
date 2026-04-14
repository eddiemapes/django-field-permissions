"""
Tests for cache-invalidation signal handlers in signals.py.

Pattern for each test:
  1. Create relevant objects and prime the cache key(s).
  2. Perform the M2M / save / delete mutation.
  3. Assert the affected cache key(s) are gone.
"""

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from field_permissions.models import FieldPermission


SENTINEL = object()  # used to distinguish "key absent" from "key = None"


def prime(user_id):
    """Write a placeholder set into a user's cache slot."""
    cache.set(f"user_field_perms_{user_id}", {("user", "email", "read")})


def is_cleared(user_id) -> bool:
    return cache.get(f"user_field_perms_{user_id}", SENTINEL) is SENTINEL


# ---------------------------------------------------------------------------
# handle_users_changed  (m2m_changed on FieldPermission.users.through)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_users_post_add_clears_user_cache(user, field_perm):
    prime(user.id)
    field_perm.users.add(user)
    assert is_cleared(user.id)


@pytest.mark.django_db
def test_users_post_remove_clears_user_cache(user, field_perm):
    field_perm.users.add(user)
    prime(user.id)
    field_perm.users.remove(user)
    assert is_cleared(user.id)


@pytest.mark.django_db
def test_users_post_clear_clears_all_user_caches(field_perm):
    u1 = User.objects.create_user(username="u1", password="pass")
    u2 = User.objects.create_user(username="u2", password="pass")
    field_perm.users.set([u1, u2])

    prime(u1.id)
    prime(u2.id)

    field_perm.users.clear()

    assert is_cleared(u1.id)
    assert is_cleared(u2.id)


# ---------------------------------------------------------------------------
# handle_groups_changed  (m2m_changed on FieldPermission.groups.through)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_groups_post_add_clears_member_caches(user, group, field_perm):
    user.groups.add(group)
    prime(user.id)
    field_perm.groups.add(group)
    assert is_cleared(user.id)


@pytest.mark.django_db
def test_groups_post_remove_clears_member_caches(user, group, field_perm):
    user.groups.add(group)
    field_perm.groups.add(group)
    prime(user.id)
    field_perm.groups.remove(group)
    assert is_cleared(user.id)


@pytest.mark.django_db
def test_groups_post_clear_clears_all_user_caches(field_perm):
    from django.contrib.auth.models import Group

    g = Group.objects.create(name="grp")
    u1 = User.objects.create_user(username="gu1", password="pass")
    u2 = User.objects.create_user(username="gu2", password="pass")
    u1.groups.add(g)
    u2.groups.add(g)
    field_perm.groups.set([g])

    prime(u1.id)
    prime(u2.id)

    field_perm.groups.clear()

    assert is_cleared(u1.id)
    assert is_cleared(u2.id)


# ---------------------------------------------------------------------------
# handle_permission_saved  (post_save on FieldPermission)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_permission_saved_clears_direct_user_cache(user):
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.users.add(user)
    prime(user.id)

    # Trigger post_save by calling save()
    perm.save()

    assert is_cleared(user.id)


@pytest.mark.django_db
def test_permission_saved_clears_group_member_caches(user, group):
    user.groups.add(group)
    perm = FieldPermission.objects.create(
        model_name="user", field_name="username", access_level="edit"
    )
    perm.groups.add(group)
    prime(user.id)

    perm.save()

    assert is_cleared(user.id)


@pytest.mark.django_db
def test_permission_saved_no_users_no_error():
    # Saving a perm with no users/groups should not raise
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="edit"
    )
    perm.save()  # no exception


# ---------------------------------------------------------------------------
# handle_permission_pre_delete + handle_permission_deleted
# (the pre_delete stash + post_delete invalidation chain)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_permission_delete_clears_direct_user_cache(user, field_perm):
    field_perm.users.add(user)
    prime(user.id)

    field_perm.delete()

    assert is_cleared(user.id)


@pytest.mark.django_db
def test_permission_delete_clears_group_member_cache(user, group):
    user.groups.add(group)
    perm = FieldPermission.objects.create(
        model_name="user", field_name="username", access_level="read"
    )
    perm.groups.add(group)
    prime(user.id)

    perm.delete()

    assert is_cleared(user.id)


@pytest.mark.django_db
def test_permission_delete_no_users_no_error():
    # Deleting a perm with no M2M relations should not raise AttributeError
    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="edit"
    )
    perm.delete()  # no exception


@pytest.mark.django_db
def test_permission_delete_both_user_and_group(user, group):
    """Both a direct user and a group member should be invalidated on delete."""
    other_user = User.objects.create_user(username="other", password="pass")
    other_user.groups.add(group)

    perm = FieldPermission.objects.create(
        model_name="user", field_name="email", access_level="read"
    )
    perm.users.add(user)
    perm.groups.add(group)

    prime(user.id)
    prime(other_user.id)

    perm.delete()

    assert is_cleared(user.id)
    assert is_cleared(other_user.id)
