from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class Tag(models.Model):
    """Метки для группировки привычек"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Метка'
        verbose_name_plural = 'Метки'
        ordering = ['name']

    def __str__(self):
        return self.name


class Habit(models.Model):
    """Привычка пользователя для отслеживания"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    target_frequency = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text='Целевое количество раз в неделю'
    )
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='habits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.user.username})'


class HabitSession(models.Model):
    """Лог выполнения привычки (сессия)"""
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habit_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        editable=False
    )
    interruptions = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Количество прерываний во время сессии'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Сессия привычки'
        verbose_name_plural = 'Сессии привычек'
        ordering = ['-start_time']

    def __str__(self):
        return f'{self.habit.title} - {self.start_time.strftime("%d.%m.%Y %H:%M")}'

    def save(self, *args, **kwargs):
        """Автоматически вычисляем duration_minutes при сохранении"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    def clean(self):
        """Валидация на уровне модели"""
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('Время окончания должно быть позже времени начала')


class ProductivityReport(models.Model):
    """Предварительно вычисленные агрегаты продуктивности по дням"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productivity_reports')
    date = models.DateField()
    total_minutes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    sessions_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    avg_session_length = models.FloatField(default=0.0, validators=[MinValueValidator(0)])
    avg_interruptions = models.FloatField(default=0.0, validators=[MinValueValidator(0)])
    focus_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0)],
        help_text='Вычисленная метрика продуктивности (0-100)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Отчёт продуктивности'
        verbose_name_plural = 'Отчёты продуктивности'
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'Report {self.user.username} - {self.date.strftime("%d.%m.%Y")}'

    @staticmethod
    def calculate_focus_score(avg_session_length, avg_interruptions, sessions_count):
        """
        Рассчитывает focus_score по формуле из ТЗ:
        focus_score = 100 * min(avg_session_length, 120) / 120 * (1 - avg_interruptions / (sessions_count + 1))
        """
        if sessions_count == 0:
            return 0.0

        session_component = min(avg_session_length, 120) / 120
        interruption_component = 1 - (avg_interruptions / (sessions_count + 1))
        focus_score = 100 * session_component * max(interruption_component, 0)
        return round(focus_score, 2)
