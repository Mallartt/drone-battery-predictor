from rest_framework import permissions


class ReadOnlyIfAnonymous(permissions.BasePermission):
    """
    Гость может только читать (GET, HEAD, OPTIONS).
    Авторизованные – в зависимости от их роли.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsModerator(permissions.BasePermission):
    """
    Доступ только для модераторов (is_staff=True).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and ( request.user.is_staff or request.user.is_superuser))
