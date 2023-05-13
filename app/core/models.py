from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class UserManager(BaseUserManager):
    """Manager for users in our system"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        user = self.create_user(email, password)
        user.isStaff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    User in our system
    """
    email = models.EmailField(max_length=255, unique=True)

    name = models.CharField(max_length=255)

    isActive = models.BooleanField(default=True)

    isStaff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
