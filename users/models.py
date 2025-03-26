from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from datetime import timedelta

class UserRoles(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "Admin"
    EXTERNAL_LAWYER = "external_lawyer", "External Lawyer"
    INTERNAL_LAWYER = "internal_lawyer", "Internal Lawyer"
    CUSTOMER = "customer", "Customer"

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role=UserRoles.CUSTOMER, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        # Ensure that superuser role cannot be overridden
        if extra_fields.get("is_superuser", False):
            role = UserRoles.SUPER_ADMIN

        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # Ensure role is set to SUPER_ADMIN
        extra_fields["role"] = UserRoles.SUPER_ADMIN

        return self.create_user(email, password, **extra_fields)

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CustomUser(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    role = models.CharField(
        max_length=20,
        choices=UserRoles.choices,
        default=UserRoles.CUSTOMER
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

class PasswordResetToken(TimestampedModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.created_at < now() - timedelta(hours=1)  # Token valid for 1 hour

    @staticmethod
    def create_token(user):
        token = get_random_string(length=64)
        return PasswordResetToken.objects.create(user=user, token=token)
