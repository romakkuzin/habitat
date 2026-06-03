from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum, Count, Avg
from django.utils import timezone

from .models import HabitSession, ProductivityReport


def _refresh_user_report(user, report_date):
    from .models import HabitSession

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
    else:
        ProductivityReport.objects.filter(user=user, date=report_date).delete()


@receiver(pre_save, sender=HabitSession)
def habit_session_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous = HabitSession.objects.get(pk=instance.pk)
            instance._previous_start_date = previous.start_time.date()
        except HabitSession.DoesNotExist:
            instance._previous_start_date = None


@receiver(post_save, sender=HabitSession)
def habit_session_post_save(sender, instance, **kwargs):
    current_date = instance.start_time.date()

    if getattr(instance, '_previous_start_date', None) and instance._previous_start_date != current_date:
        _refresh_user_report(instance.user, instance._previous_start_date)

    _refresh_user_report(instance.user, current_date)


@receiver(post_delete, sender=HabitSession)
def habit_session_post_delete(sender, instance, **kwargs):
    _refresh_user_report(instance.user, instance.start_time.date())
