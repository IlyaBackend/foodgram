from django.core.validators import RegexValidator
from rest_framework import serializers

from .constants import ERROR_USERNAME_SYMBOLS, REGULAR_USERNAME


def validate_image(value):
    if value in ('', None):
        raise serializers.ValidationError('Пустое поле image недопустимо.')
    return value


USERNAME_REGEX_VALIDATOR = RegexValidator(
    regex=REGULAR_USERNAME,
    message=ERROR_USERNAME_SYMBOLS
)
