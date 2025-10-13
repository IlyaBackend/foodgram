import json
import os

from django.core.management.base import BaseCommand, CommandError


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON."""

    model = None
    default_file = 'default.json'
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
            abs_path = os.path.join(os.getcwd(), self.file_path)
            with open(abs_path, encoding='utf-8') as f:
                self.stdout.write(self.style.SUCCESS(
                    'Импорт завершён добавлено {} записей из файла {}'.format(
                        len(set(
                            self.model.objects.bulk_create(
                                (self.model(**item) for item in json.load(f)),
                                ignore_conflicts=True
                            ))), os.path.basename(self.file_path))))
        except Exception as e:
            raise CommandError(
                f'Ошибка при выполнении импорта: '
                f'{self.file_path}: {e}'
            ) from e
