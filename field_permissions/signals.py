from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed, post_save, pre_delete, post_delete
from django.dispatch import receiver

from field_permissions.models import FieldPermission


def invalidate_user_cache(user_ids):
    keys = [f'user_field_perms_{uid}' for uid in user_ids]
    if keys:
        cache.delete_many(keys)


@receiver(m2m_changed, sender=FieldPermission.users.through)
def handle_users_changed(sender, instance, action, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    if pk_set:
        invalidate_user_cache(pk_set)
    else:
        all_ids = User.objects.values_list('id', flat=True)
        invalidate_user_cache(all_ids)


@receiver(m2m_changed, sender=FieldPermission.groups.through)
def handle_groups_changed(sender, instance, action, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    if pk_set:
        user_ids = User.objects.filter(
            groups__id__in=pk_set
        ).values_list('id', flat=True)
        invalidate_user_cache(user_ids)
    else:
        all_ids = User.objects.values_list('id', flat=True)
        invalidate_user_cache(all_ids)


@receiver(post_save, sender=FieldPermission)
def handle_permission_saved(sender, instance, **kwargs):
    user_ids = set(instance.users.values_list('id', flat=True))
    group_user_ids = set(
        User.objects.filter(
            groups__in=instance.groups.all()
        ).values_list('id', flat=True)
    )
    invalidate_user_cache(user_ids | group_user_ids)


@receiver(pre_delete, sender=FieldPermission)
def handle_permission_pre_delete(sender, instance, **kwargs):
    instance._cached_user_ids = set(instance.users.values_list('id', flat=True))
    instance._cached_group_user_ids = set(
        User.objects.filter(
            groups__in=instance.groups.all()
        ).values_list('id', flat=True)
    )


@receiver(post_delete, sender=FieldPermission)
def handle_permission_deleted(sender, instance, **kwargs):
    user_ids = getattr(instance, '_cached_user_ids', set())
    group_user_ids = getattr(instance, '_cached_group_user_ids', set())
    invalidate_user_cache(user_ids | group_user_ids)
