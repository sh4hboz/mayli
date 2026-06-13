"""
accounts/permissions.py

BOSQICH 0.5 — DRF RBAC permission klasslari.

Foydalanish:
    from accounts.permissions import IsOwner, IsManager, IsStaff, IsCustomer

    class MyView(APIView):
        permission_classes = [IsAuthenticated, IsManager]
"""

from rest_framework.permissions import BasePermission
from .models import Role


def _get_role(user) -> str:
    """
    Foydalanuvchi rolini qaytaradi (accounts.User.role).
    """
    if not user.is_authenticated:
        return Role.CUSTOMER
    return getattr(user, 'role', Role.CUSTOMER)


class IsOwner(BasePermission):
    """Faqat ega (owner) ruxsat."""
    message = 'Faqat ega uchun!'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request.user) in (
            Role.OWNER, Role.ADMIN
        )


class IsManager(BasePermission):
    """Menejer va undan yuqori ruxsat."""
    message = 'Faqat menejer va undan yuqori rol uchun!'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request.user) in (
            Role.MANAGER, Role.OWNER, Role.ADMIN
        )


class IsAccountant(BasePermission):
    """Bugalter va undan yuqori ruxsat."""
    message = 'Faqat bugalter va undan yuqori rol uchun!'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request.user) in (
            Role.ACCOUNTANT, Role.MANAGER, Role.OWNER, Role.ADMIN
        )


class IsStaff(BasePermission):
    """Har qanday xodim ruxsati (ofitsiant, barman, bugalter, menejer, ega)."""
    message = 'Faqat xodimlar uchun!'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return _get_role(request.user) not in (Role.CUSTOMER,)


class IsWaiter(BasePermission):
    """Ofitsiant va undan yuqori ruxsat."""
    message = 'Faqat ofitsiant va undan yuqori rol uchun!'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request.user) in (
            Role.WAITER, Role.BARMAN, Role.ACCOUNTANT, Role.MANAGER, Role.OWNER, Role.ADMIN
        )


class IsCustomer(BasePermission):
    """Faqat mijoz ruxsati."""
    message = 'Faqat mijozlar uchun!'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request.user) == Role.CUSTOMER


class IsOwnerOrReadOnly(BasePermission):
    """Faqat ega o'zgartira oladi, boshqalar faqat o'qiydi."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_authenticated and _get_role(request.user) in (
            Role.OWNER, Role.ADMIN
        )
