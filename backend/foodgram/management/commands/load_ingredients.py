import csv
import json
import os

from django.core.management.base import BaseCommand, CommandError

from foodgram.models import Ingredients


class Command(BaseCommand):
    help = (
        'Загружает ингредиенты из JSON или CSV файла в базу данных. '
        'Если таблица уже содержит данные, загрузка пропускается.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Путь к файлу (например: data/ingredients.json)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        # Проверка — если ингредиенты уже есть, прекращаем выполнение
        if Ingredients.objects.exists():
            total = Ingredients.objects.count()
            self.stdout.write(self.style.WARNING(
                f'Таблица Ingredients уже содержит {total} записей.'
                f'Загрузка пропущена.'
            ))
            return
        # Абсолютный путь (чтобы работало в Docker)
        abs_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(abs_path):
            raise CommandError(f'Файл не найден: {abs_path}')
        added, skipped = 0, 0
        try:
            if file_path.endswith('.json'):
                with open(abs_path, encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        name = item.get('name', '').strip()
                        unit = item.get('measurement_unit', '').strip()
                        if not name or not unit:
                            skipped += 1
                            continue
                        Ingredients.objects.get_or_create(
                            name=name,
                            measurement_unit=unit
                        )
                        added += 1
            elif file_path.endswith('.csv'):
                with open(abs_path, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) < 2:
                            skipped += 1
                            continue
                        name, unit = row[0].strip(), row[1].strip()
                        if not name or not unit:
                            skipped += 1
                            continue
                        Ingredients.objects.get_or_create(
                            name=name,
                            measurement_unit=unit
                        )
                        added += 1
            else:
                raise CommandError(
                    'Поддерживаются только файлы .json или .csv')
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise CommandError(f'Ошибка чтения файла: {e}')
        self.stdout.write(self.style.SUCCESS('Загрузка завершена!'))
        self.stdout.write(f'Добавлено записей: {added}')
        if skipped:
            self.stdout.write(
                f'Пропущено (пустые строки или ошибки): {skipped}')
