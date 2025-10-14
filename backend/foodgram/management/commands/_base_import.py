import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON."""

    model = None
    default_file = ''
    file_help = ''
    file_path = ''

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help=self.file_help,
        )

    def handle(self, *args, **options):
        self.file_path = options.get('file') or self.default_file
        try:
            abs_path = Path.cwd() / self.file_path
            with abs_path.open(encoding='utf-8') as f:
                created = self.model.objects.bulk_create((
                    self.model(**item) for item in json.load(f)
                ), ignore_conflicts=True
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Импорт завершён добавлены все {len(created)} '
                    f'записей из файла {abs_path.name}'))
        except Exception as e:
            raise CommandError(
                f'Ошибка при выполнении импорта: '
                f'{self.file_path}: {e}'
            ) from e
