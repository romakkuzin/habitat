from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from dashboard.models import Habit, HabitSession, ProductivityReport

User = get_user_model()


class HabitSessionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bob', password='pw')
        self.habit = Habit.objects.create(
            user=self.user,
            title='Test habit',
            target_frequency=3,
        )

    def test_duration_minutes_is_computed_on_save(self):
        start = timezone.now()
        end = start + timedelta(minutes=45)
        session = HabitSession.objects.create(
            habit=self.habit,
            user=self.user,
            start_time=start,
            end_time=end,
            interruptions=1,
        )
        self.assertEqual(session.duration_minutes, 45)

    def test_end_time_must_be_later_than_start_time(self):
        start = timezone.now()
        end = start - timedelta(minutes=5)
        session = HabitSession(
            habit=self.habit,
            user=self.user,
            start_time=start,
            end_time=end,
            interruptions=0,
        )
        with self.assertRaises(ValidationError):
            session.full_clean()


class ProductivityReportTests(TestCase):
    def test_focus_score_formula_returns_zero_for_no_sessions(self):
        result = ProductivityReport.calculate_focus_score(0, 0, 0)
        self.assertEqual(result, 0.0)

    def test_focus_score_formula_scales_correctly(self):
        score = ProductivityReport.calculate_focus_score(60, 1, 2)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
