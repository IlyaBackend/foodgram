from foodgram.models import Tag

from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт тегов из JSON файла в базу данных.'
    model = Tag
    file_help = 'Путь к файлу (например: data/tags.json)'
