from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from field_permissions.models import FieldPermission


class FieldPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        enabled = getattr(settings, 'FIELD_PERMISSIONS_ENABLE', True)
        # Exit early if field permissions are not enabled 
        if not enabled:
            response = self.get_response(request)
            return response

        # Exit early if user is not authenticated 
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            response = self.get_response(request)
            return response

        use_cache = getattr(settings, 'FIELD_PERMISSIONS_USE_CACHE', True)
        cache_timeout = getattr(settings, 'FIELD_PERMISSIONS_CACHE_TIMEOUT', 3600)
        user = request.user
        cache_key = f'user_field_perms_{user.id}'

        if use_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                request.field_perms = cached
                response = self.get_response(request)
                return response

        user_groups = user.groups.all()
        field_perms = set(
            FieldPermission.objects.filter(
                Q(users=user) | Q(groups__in=user_groups)
            ).values_list('model_name', 'field_name', 'access_level')
        )

        if use_cache:
            cache.set(cache_key, field_perms, cache_timeout)

        request.field_perms = field_perms
        response = self.get_response(request)
        return response
