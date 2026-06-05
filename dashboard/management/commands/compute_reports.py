from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from dashboard.models import HabitSession, ProductivityReport


class Command(BaseCommand):
    help = 'Вычисляет и сохраняет дневные отчёты продуктивности для пользователей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Количество дней назад, за которые нужно пересчитать отчёты',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Дата начала расчёта в формате YYYY-MM-DD',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='Дата окончания расчёта в формате YYYY-MM-DD',
        )

    def handle(self, *args, **options):
        now = timezone.localdate()
        start_date = None
        end_date = None

        if options['start_date']:
            start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
        if options['end_date']:
            end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()

        if not end_date:
            end_date = now
        if not start_date:
            start_date = end_date - timedelta(days=options['days'] - 1)

        if start_date > end_date:
            raise ValueError('start_date не может быть позже end_date')

        self.stdout.write(f'Пересчёт отчётов за период: {start_date} — {end_date}')
        User = get_user_model()
        users = User.objects.all()

        for user in users:
            self.stdout.write(f'Обработка пользователя: {user.username}')
            for offset in range((end_date - start_date).days + 1):
                report_date = start_date + timedelta(days=offset)
                stats = HabitSession.objects.filter(
                    user=user,
                    start_time__date=report_date
                ).aggregate(
                    total_minutes=Sum('duration_minutes'),
                    sessions_count=Count('id'),
                    avg_session_length=Avg('duration_minutes'),
                    avg_interruptions=Avg('interruptions'),
                )

                total_minutes = stats['total_minutes'] or 0
                sessions_count = stats['sessions_count'] or 0
                avg_session_length = stats['avg_session_length'] or 0
                avg_interruptions = stats['avg_interruptions'] or 0
                focus_score = ProductivityReport.calculate_focus_score(
                    avg_session_length,
                    avg_interruptions,
                    sessions_count,
                )

                if sessions_count > 0:
                    ProductivityReport.objects.update_or_create(
                        user=user,
                        date=report_date,
                        defaults={
                            'total_minutes': total_minutes,
                            'sessions_count': sessions_count,
                            'avg_session_length': avg_session_length,
                            'avg_interruptions': avg_interruptions,
                            'focus_score': focus_score,
                        }
                    )
                    self.stdout.write(f'  Обновлён отчёт за {report_date}: {total_minutes} мин, {sessions_count} сессий, focus {focus_score}')
                else:
                    deleted, _ = ProductivityReport.objects.filter(user=user, date=report_date).delete()
                    if deleted:
                        self.stdout.write(f'  Удалён пустой отчёт за {report_date}')

            # Опционально: вычислим скользящие средние focus_score за период, если установлен pandas
            try:
                import pandas as pd
            except Exception:
                pd = None

            if pd:
                reports_qs = ProductivityReport.objects.filter(user=user, date__range=(start_date, end_date)).order_by('date')
                if reports_qs.exists():
                    df = pd.DataFrame(list(reports_qs.values('date', 'focus_score')))
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date').sort_index()
                    for window in (7, 14, 30):
                        col = f'rolling_focus_{window}'
                        df[col] = df['focus_score'].rolling(window=window, min_periods=1).mean()
                    # Выведем краткую статистику для информации
                    last = df.iloc[-1]
                    self.stdout.write(f"  Rolling focus (last) for {user.username}: 7d={last.get('rolling_focus_7'):.2f}, 14d={last.get('rolling_focus_14'):.2f}, 30d={last.get('rolling_focus_30'):.2f}")

        self.stdout.write(self.style.SUCCESS('✓ Расчёт отчётов завершён.'))
