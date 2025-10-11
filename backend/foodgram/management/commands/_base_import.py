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
        if self.model is None:
            raise CommandError('Не указана модель для импорта.')
        self.file_path = options['file']
        try:
            abs_path = os.path.join(os.getcwd(), self.file_path)
            if not os.path.exists(abs_path):
                raise CommandError(f'Файл не найден: {abs_path}')
            with open(abs_path, encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise CommandError('Формат JSON должен быть списком объектов.')
            if self.model.objects.exists():
                total = self.model.objects.count()
                self.stdout.write(self.style.WARNING(
                    f'Таблица {self.model.__name__} уже содержит'
                    f'{total} записей. Загрузка пропущена.'
                ))
                return
            objects = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                if not all(item.values()):
                    continue
                objects.append(self.model(**item))
            if not objects:
                raise CommandError('Нет корректных данных для импорта.')
            self.model.objects.bulk_create(objects, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Импорт завершён: добавлено {len(objects)} записей из файла'
                f'{os.path.basename(self.file_path)}.'
            ))
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            CommandError,
            Exception
        ) as e:
            raise CommandError(f'Ошибка при выполнении импорта: {e}')
