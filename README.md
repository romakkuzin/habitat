# Habitat

## Описание проекта

Этот проект — веб-сервис `Habitat` для анализа привычек пользователя и расчёта персонального уровня продуктивности. Он позволяет:

- создавать и управлять привычками (`Habit`)
- логировать сессии выполнения (`HabitSession`)
- автоматически вычислять длительность сессий и показатели продуктивности
- собирать и хранить ежедневные отчёты в `ProductivityReport`
- просматривать графики и аналитику через Django-шаблоны
- работать с REST API через Django REST Framework
- использовать кастомный панель администратора без стандартной Django admin UI

## Архитектура

### Основные компоненты

- `core/`: основной Django-проект
  - `settings.py`: настройка проекта и подключение приложений
  - `urls.py`: маршруты проекта, в том числе кастомная админ-панель `/manage/`

- `dashboard/`: основное приложение
  - `models.py`: бизнес-модели `Tag`, `Habit`, `HabitSession`, `ProductivityReport`
  - `views.py`: пользовательские страницы, API и кастомная admin UI
  - `serializers.py`: DRF-сериализаторы для API
  - `forms.py`: формы регистрации, логина, создания привычек и сессий
  - `signals.py`: автоматическое обновление отчётов при изменении сессий
  - `management/commands/`: утилиты для генерации данных и пересчёта отчётов
  - `templates/dashboard/`: интерфейс пользователя и аналитика

### Ключевая логика

- `HabitSession.save()`: рассчитывает `duration_minutes` автоматически
- `signals.py`: обновляет `ProductivityReport` при создании, редактировании и удалении сессий
- `compute_reports`: management-команда для пересчёта ежедневных отчетов
- `generate_fixtures`: команда для заполнения демонстрационных данных
- `dashboard.views.dashboard_view`: собирает аналитику по сессиям для отображения на пользовательском дашборде
- кастомная админ-панель `/manage/`: список пользователей, привычек, сессий с пагинацией, bulk actions и CSV экспортом

## Установка и локальный запуск

### Требования

- Python 3.11+ (рекомендуется 3.13)
- SQLite (по умолчанию использует `db.sqlite3`)
- `pip`

### Установка на Linux / macOS

```bash
cd /home/unusualnick/Desktop/programming/personal/roma/django
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env при необходимости
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Установка на Windows

```powershell
cd C:\path\to\django
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
# Отредактируйте .env при необходимости
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Дополнительные команды

- `python manage.py test` — запуск тестов проекта
- `python manage.py generate_fixtures` — создать демонстрационные данные
- `python manage.py compute_reports --days 30` — пересчитать отчёты за последние 30 дней

## Переменные окружения

Файл `.env` должен содержать:

- `DJANGO_SECRET_KEY` — секретный ключ Django
- `DJANGO_DEBUG` — `True` или `False`
- `DJANGO_ALLOWED_HOSTS` — список хостов через запятую

## Ключевые URL

- `/` — главная страница
- `/register/` — регистрация пользователя
- `/login/` — страница логина
- `/dashboard/` — личный дашборд
- `/habits/` — управление привычками
- `/reports/` — отчёты и графики
- `/manage/` — кастомная панель администратора для staff-пользователей

## Примечания

- `DEBUG` по умолчанию выключен и управляется переменной `DJANGO_DEBUG`
- `.env` не должна попадать в репозиторий
- `.env.example` содержит шаблон нужных переменных окружения
