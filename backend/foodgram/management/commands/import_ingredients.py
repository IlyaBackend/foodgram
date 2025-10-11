from foodgram.models import Ingredients

from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт ингредиентов из JSON файла в базу данных.'
    model = Ingredients
    file_help = 'Путь к файлу (например: data/ingredients.json)'
