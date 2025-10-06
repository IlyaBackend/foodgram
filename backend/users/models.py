from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.constants import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH
from backend.validators import username_regex_validator, validate_username


class Account(AbstractUser):
    """Кастомная модель пользователя."""

    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(validate_username, username_regex_validator),
        verbose_name='Имя пользователя'
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Email'
    )
    avatar = models.ImageField(
        upload_to='users',
        null=True,
        blank=True,
        default=None,
        verbose_name='Аватар'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)


class Subscription(models.Model):
    """Модель подписок, на кого я подписан и кто подписна на меня."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers',
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
