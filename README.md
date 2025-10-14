# Foodgram

**Foodgram** - Это социальная платформа для обмена рецептами и для тех кто любит вкусно покушать и всегда хочет знать что ему для этого надо

Здесь пользователи могут:
- Доьбавлять свои фирменные рецепты;
- Указывать точное количество ингредиентов для приготовления
- Пользоваться тэгами для быстрого поиска рецептов
- Подписываться на авторов, чья еда больше всего запомнилась
- Добавлять в избранное любимые рецепты
- Получать точный список ингредиентов для покупки в удобном txt формате

---

## Стек технологий

- **Backend:** Python, Django, Django REST Framework, Gunicorn  
- **Frontend:** React, JavaScript, CSS  
- **База данных:** PostgreSQL  
- **Веб-сервер:** Nginx  
- **Контейнеризация:** Docker, Docker Compose  
- **CI/CD:** GitHub Actions *(опционально)*  

---

##  Развёртывание проекта

### 1. Клонировать репозиторий
```bash
git clone https://github.com/IlyaBackend/foodgram.git
cd foodgram
```
### 2. Создать .env файл в корне проекта

Пример содержимого см. ниже.

### 3. Собрать и запустить контейнеры
```bash
docker compose up -d --build
```

### 4. Выполнить миграции и собрать статику
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
```

### 5. Создать суперпользователя
```bash
docker compose exec backend python manage.py createsuperuser
```

### 6. Удобно самостоятельно загрузить ингредиенты в БД (Опционально)
- ингредиениы
```bash
docker compose exec backend python manage.py import_ingredients --file data/ingredients.json
```
- тэги
```bash
docker compose exec backend python manage.py import_tags --file data/tags.json
```
### После этого проект будет доступен по адресу:
http://[<ваш_серверный_IP>](http://localhost:8000/)/

## Документация API
[http://localhost/api/docs/](http://localhost/api/docs/)

# Переменные окружения (.env)

Создайте файл .env в корне проекта и добавьте туда:

# Django
- SECRET_KEY=Ваш SECRET_KEY
- DEBUG=False или True
- ALLOWED_HOSTS=localhost, Ваш_домен
- CSRF_TRUSTED_ORIGINS=Ваш htpp и htpps домен

Возможность подключить sqlite по необходимости
- USE_SQLITE=False или True

# Database
- POSTGRES_DB=Название_вашей_DB
- POSTGRES_USER=Ваш_postgres_username
- POSTGRES_PASSWORD=Ваш_postgres_password
- DB_HOST=db
- DB_PORT=5432

---

## Локальный запуск без Docker

Если Docker не используется:
```bash
git clone https://github.com/IlyaBackend/foodgram.git
cd foodgram/backend
```


```bash
# Установка зависимостей
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Миграции и запуск
python manage.py migrate
python manage.py runserver
```

После этого проект будет доступен по адресу:  
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Автор 

Проект выполнен в рамках учебного спринта **Яндекс.Практикума**.
**Автор:** Кучеревский Илья Олегович
Tg: [https://t.me/mbifckumm](https://t.me/mbifckumm)

[IlyaBackend](https://github.com/IlyaBackend)
