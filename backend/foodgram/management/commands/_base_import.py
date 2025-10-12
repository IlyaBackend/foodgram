import json
import os

from django.core.management.base import BaseCommand, CommandError


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON."""

    model = None
    file_help = ''
    file_path = ''

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help=self.file_help,
        )

    def handle(self, *args, **options):
        self.file_path = options['file']
        try:
            abs_path = os.path.join(os.getcwd(), self.file_path)
            with open(abs_path, encoding='utf-8') as f:
                objects = [self.model(**item) for item in json.load(f)]
            self.model.objects.bulk_create(objects, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Импорт завершён: добавлено {len(set(objects))} '
                f'записей из файла {os.path.basename(self.file_path)}.'
            ))
        except Exception as e:
            raise CommandError(
                f'Ошибка при выполнении импорта: '
                f'{self.file_path}: {e}'
            ) from e
