from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from dashboard.models import Habit, ProductivityReport

User = get_user_model()


class DashboardViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw', email='alice@example.com')
        self.client.login(username='alice', password='pw')

    def test_dashboard_view_returns_context(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('habit_count', response.context)
        self.assertIn('avg_focus_score', response.context)

    def test_habit_create_and_detail(self):
        response = self.client.post(reverse('habit_create'), {
            'title': 'New Habit',
            'description': 'Описание привычки',
            'target_frequency': 4,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        habit = Habit.objects.get(user=self.user, title='New Habit')
        detail_response = self.client.get(reverse('habit_detail', args=[habit.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'New Habit')

    def test_reports_view_shows_reports(self):
        ProductivityReport.objects.create(
            user=self.user,
            date='2026-06-16',
            total_minutes=60,
            sessions_count=1,
            avg_session_length=60.0,
            avg_interruptions=0.0,
            focus_score=75.0,
        )
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Отчёты продуктивности')
        self.assertContains(response, '75.0')
