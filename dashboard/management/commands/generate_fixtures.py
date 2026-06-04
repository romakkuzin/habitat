from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from dashboard.models import Tag, Habit, HabitSession, ProductivityReport
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Генерирует тестовые данные для демонстрации'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем генерацию тестовых данных...')

        # Очищаем старые данные
        Tag.objects.all().delete()
        Habit.objects.all().delete()
        HabitSession.objects.all().delete()
        ProductivityReport.objects.all().delete()

        # Создаём пользователей
        demo_password = 'demo1234'

        user1, created = User.objects.get_or_create(
            username='test_user1',
            defaults={'email': 'user1@example.com'}
        )
        if created or not user1.has_usable_password():
            user1.set_password(demo_password)
            user1.save()

        user2, created = User.objects.get_or_create(
            username='test_user2',
            defaults={'email': 'user2@example.com'}
        )
        if created or not user2.has_usable_password():
            user2.set_password(demo_password)
            user2.save()

        # Создаём метки
        tags_names = ['Спорт', 'Учёба', 'Работа', 'Чтение', 'Медитация', 'Программирование']
        tags = []
        for name in tags_names:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace(' ', '-')}
            )
            tags.append(tag)

        # Создаём привычки для user1
        habits_user1_data = [
            {'title': 'Утренняя зарядка', 'description': 'Упражнения по 20 минут каждое утро', 'target_frequency': 7, 'tags': [tags[0]]},
            {'title': 'Изучение Python', 'description': 'Ежедневное обучение программированию', 'target_frequency': 5, 'tags': [tags[4], tags[5]]},
            {'title': 'Чтение технических статей', 'description': 'Подержание актуальности знаний', 'target_frequency': 3, 'tags': [tags[3], tags[5]]},
        ]
        habits_user1 = []
        for habit_data in habits_user1_data:
            tags_list = habit_data.pop('tags')
            habit = Habit.objects.create(user=user1, **habit_data)
            habit.tags.set(tags_list)
            habits_user1.append(habit)

        # Создаём привычки для user2
        habits_user2_data = [
            {'title': 'Йога', 'description': 'Ежедневная практика йоги', 'target_frequency': 6, 'tags': [tags[0]]},
            {'title': 'Работа над проектом', 'description': 'Интенсивная работа', 'target_frequency': 5, 'tags': [tags[1], tags[2]]},
        ]
        habits_user2 = []
        for habit_data in habits_user2_data:
            tags_list = habit_data.pop('tags')
            habit = Habit.objects.create(user=user2, **habit_data)
            habit.tags.set(tags_list)
            habits_user2.append(habit)

        # Генерируем сессии за последние 30 дней для user1
        now = timezone.now()
        for habit in habits_user1:
            for days_ago in range(30):
                date = now - timedelta(days=days_ago)
                if random.random() > 0.3:  # 70% вероятность выполнения
                    start = date.replace(hour=random.randint(6, 18), minute=random.randint(0, 59))
                    duration = random.randint(15, 90)
                    end = start + timedelta(minutes=duration)
                    interruptions = random.randint(0, 5)

                    session = HabitSession.objects.create(
                        habit=habit,
                        user=user1,
                        start_time=start,
                        end_time=end,
                        interruptions=interruptions,
                        notes='Автоматически сгенерировано' if random.random() > 0.7 else ''
                    )
                    self.stdout.write(f'  Создана сессия: {session}')

        # Генерируем сессии за последние 30 дней для user2
        for habit in habits_user2:
            for days_ago in range(30):
                date = now - timedelta(days=days_ago)
                if random.random() > 0.25:  # 75% вероятность выполнения
                    start = date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
                    duration = random.randint(20, 120)
                    end = start + timedelta(minutes=duration)
                    interruptions = random.randint(0, 3)

                    session = HabitSession.objects.create(
                        habit=habit,
                        user=user2,
                        start_time=start,
                        end_time=end,
                        interruptions=interruptions,
                        notes='Продуктивная сессия' if random.random() > 0.8 else ''
                    )
                    self.stdout.write(f'  Создана сессия: {session}')

        self.stdout.write(self.style.SUCCESS('✓ Тестовые данные успешно созданы!'))
        self.stdout.write(f'  Пользователи: {User.objects.count()}')
        self.stdout.write(f'  Метки: {Tag.objects.count()}')
        self.stdout.write(f'  Привычки: {Habit.objects.count()}')
        self.stdout.write(f'  Сессии: {HabitSession.objects.count()}')

        # Пересчитываем отчёты после генерации данных.
        from django.core.management import call_command
        call_command('compute_reports', '--days', '30')
