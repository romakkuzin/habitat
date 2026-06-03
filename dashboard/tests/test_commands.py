from datetime import timedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from dashboard.models import Habit, HabitSession, ProductivityReport

User = get_user_model()


class ComputeReportsCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw')
        self.habit = Habit.objects.create(
            user=self.user,
            title='Daily reading',
            target_frequency=4,
        )
        now = timezone.now()
        HabitSession.objects.create(
            habit=self.habit,
            user=self.user,
            start_time=now - timedelta(hours=1),
            end_time=now,
            interruptions=0,
        )

    def test_compute_reports_command_creates_report(self):
        call_command('compute_reports', '--days', '1')
        report = ProductivityReport.objects.filter(user=self.user).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.sessions_count, 1)
        self.assertGreater(report.total_minutes, 0)
