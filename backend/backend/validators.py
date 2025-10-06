from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator

from .constants import (ERROR_MESSAGE_EMAIL_IS_BUSY, ERROR_USERNAME_IS_BUISY,
                        ERROR_USERNAME_SYMBOLS, MY_USER_PROFILE,
                        REGULAR_USERNAME)


def validate_username(value):
    if value.lower() == MY_USER_PROFILE:
        raise ValidationError(
            f'Нельзя использовать {MY_USER_PROFILE} в качестве username'
        )


def unique_email_validator():
    """Проверка уникальности email."""
    return UniqueValidator(
        queryset=get_user_model().objects.all(),
        message=ERROR_MESSAGE_EMAIL_IS_BUSY
    )


def unique_username_validator():
    """Проверка уникальности username."""
    return UniqueValidator(
        queryset=get_user_model().objects.all(),
        message=ERROR_USERNAME_IS_BUISY
    )


username_regex_validator = RegexValidator(
    regex=REGULAR_USERNAME,
    message=ERROR_USERNAME_SYMBOLS
)
