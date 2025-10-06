from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator

from .constants import MY_USER_PROFILE, REGULAR_USERNAME


def validate_username(value):
    if value.lower() == MY_USER_PROFILE:
        raise ValidationError(
            f'Нельзя использовать {MY_USER_PROFILE} в качестве username'
        )


def unique_email_validator():
    """Проверка уникальности email."""
    return UniqueValidator(
        queryset=get_user_model().objects.all(),
        message='Пользователь с таким email уже существует'
    )


def unique_username_validator():
    """Проверка уникальности username."""
    return UniqueValidator(
        queryset=get_user_model().objects.all(),
        message='Пользователь с таким именем уже существует'
    )


username_regex_validator = RegexValidator(
    regex=REGULAR_USERNAME,
    message=(
        'Имя пользователя может содержать буквы, цифры, и некоторые знаки'
    )
)
