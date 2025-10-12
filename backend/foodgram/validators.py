from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .constants import ERROR_USERNAME_SYMBOLS, REGULAR_USERNAME


def validate_image(value):
    if value in ('', None):
        raise ValidationError('Пустое поле image недопустимо.')
    return value


USERNAME_REGEX_VALIDATOR = RegexValidator(
    regex=REGULAR_USERNAME,
    message=ERROR_USERNAME_SYMBOLS
)
