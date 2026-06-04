import json
from datetime import timedelta

from django.db.models import Count, Sum, Avg, Q, F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import RegistrationForm, LoginForm, HabitForm, HabitSessionForm

from .forms import RegistrationForm, LoginForm
from .models import Habit, HabitSession, Tag, ProductivityReport
from .serializers import (
    HabitSerializer, HabitDetailSerializer, HabitSessionSerializer,
    TagSerializer, ProductivityReportSerializer
)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с метками привычек"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    search_fields = ['name']
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class HabitViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с привычками пользователя"""
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['created_at', 'title', 'target_frequency']
    ordering = ['-created_at']

    def get_queryset(self):
        """Возвращает привычки только текущего пользователя"""
        return Habit.objects.filter(user=self.request.user).prefetch_related('tags')

    def get_serializer_class(self):
        """Использует расширенный сериализатор для retrieve"""
        if self.action == 'retrieve':
            return HabitDetailSerializer
        return HabitSerializer

    def perform_create(self, serializer):
        """Автоматически устанавливает текущего пользователя"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Получить все сессии для конкретной привычки"""
        habit = self.get_object()
        sessions = habit.sessions.all()
        serializer = HabitSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Получить статистику по привычке за последние 30 дней"""
        habit = self.get_object()
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        sessions = habit.sessions.filter(start_time__gte=thirty_days_ago)
        stats = sessions.aggregate(
            total_sessions=Count('id'),
            total_minutes=Sum('duration_minutes'),
            avg_session_length=Avg('duration_minutes'),
            avg_interruptions=Avg('interruptions'),
            min_duration=Avg('duration_minutes'),  # Will compute manually
        )

        if stats['total_sessions'] > 0:
            focus_score = ProductivityReport.calculate_focus_score(
                stats['avg_session_length'] or 0,
                stats['avg_interruptions'] or 0,
                stats['total_sessions']
            )
        else:
            focus_score = 0

        return Response({
            'habit_id': habit.id,
            'habit_title': habit.title,
            'period': 'last 30 days',
            'total_sessions': stats['total_sessions'],
            'total_minutes': stats['total_minutes'] or 0,
            'avg_session_length': round(stats['avg_session_length'] or 0, 2),
            'avg_interruptions': round(stats['avg_interruptions'] or 0, 2),
            'focus_score': focus_score,
            'compliance_rate': round((stats['total_sessions'] / (habit.target_frequency * 4.28)) * 100, 2) if habit.target_frequency > 0 else 0,
        })


class HabitSessionViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с сессиями привычек"""
    serializer_class = HabitSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['habit', 'user']
    ordering_fields = ['start_time', 'created_at', 'duration_minutes']
    ordering = ['-start_time']

    def get_queryset(self):
        """Возвращает сессии только текущего пользователя"""
        user = self.request.user
        return HabitSession.objects.filter(user=user).select_related('habit', 'user')

    def perform_create(self, serializer):
        """Автоматически устанавливает текущего пользователя"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Получить сессии за сегодня"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        sessions = self.get_queryset().filter(
            start_time__gte=today_start,
            start_time__lt=today_end
        )
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Получить общую статистику пользователя за последние 30 дней"""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        sessions = self.get_queryset().filter(start_time__gte=thirty_days_ago)
        stats = sessions.aggregate(
            total_sessions=Count('id'),
            total_minutes=Sum('duration_minutes'),
            avg_session_length=Avg('duration_minutes'),
            avg_interruptions=Avg('interruptions'),
        )

        if stats['total_sessions'] > 0:
            focus_score = ProductivityReport.calculate_focus_score(
                stats['avg_session_length'] or 0,
                stats['avg_interruptions'] or 0,
                stats['total_sessions']
            )
        else:
            focus_score = 0

        return Response({
            'period': 'last 30 days',
            'total_sessions': stats['total_sessions'],
            'total_minutes': stats['total_minutes'] or 0,
            'avg_session_length': round(stats['avg_session_length'] or 0, 2),
            'avg_interruptions': round(stats['avg_interruptions'] or 0, 2),
            'focus_score': focus_score,
        })


class ProductivityReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра отчётов продуктивности (только чтение)"""
    serializer_class = ProductivityReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date', 'user']
    ordering_fields = ['date', 'focus_score', 'total_minutes']
    ordering = ['-date']

    def get_queryset(self):
        """Возвращает отчёты только текущего пользователя"""
        return ProductivityReport.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Получить сводку по фокус-скорам за последние периоды"""
        now = timezone.now()
        user = request.user

        periods = {
            'last_7_days': now - timedelta(days=7),
            'last_14_days': now - timedelta(days=14),
            'last_30_days': now - timedelta(days=30),
        }

        summary = {}
        for period_name, start_date in periods.items():
            reports = ProductivityReport.objects.filter(
                user=user,
                date__gte=start_date.date()
            )
            avg_focus = reports.aggregate(Avg('focus_score'))['focus_score__avg'] or 0
            summary[period_name] = {
                'avg_focus_score': round(avg_focus, 2),
                'report_count': reports.count(),
                'total_minutes': reports.aggregate(Sum('total_minutes'))['total_minutes__sum'] or 0,
            }

        return Response(summary)


def home(request):
    return render(request, 'dashboard/home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'dashboard/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = LoginForm(request)

    return render(request, 'dashboard/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def habit_list(request):
    habits = Habit.objects.filter(user=request.user).prefetch_related('tags').order_by('-created_at')
    return render(request, 'dashboard/habit_list.html', {'habits': habits})


@login_required
def habit_detail(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    sessions = habit.sessions.order_by('-start_time')
    return render(request, 'dashboard/habit_detail.html', {
        'habit': habit,
        'sessions': sessions,
    })


@login_required
def habit_create(request):
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            form.save_m2m()
            return redirect('habit_detail', pk=habit.pk)
    else:
        form = HabitForm()
    return render(request, 'dashboard/habit_form.html', {'form': form, 'title': 'Создать привычку'})


@login_required
def habit_edit(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            return redirect('habit_detail', pk=habit.pk)
    else:
        form = HabitForm(instance=habit)
    return render(request, 'dashboard/habit_form.html', {'form': form, 'title': 'Редактировать привычку'})


@login_required
def habit_delete(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if request.method == 'POST':
        habit.delete()
        return redirect('habit_list')
    return render(request, 'dashboard/confirm_delete.html', {
        'object': habit,
        'title': 'Удалить привычку',
        'cancel_url': 'habit_detail',
        'cancel_args': [habit.pk],
    })


@login_required
def session_create(request, habit_pk=None):
    habit = None
    if habit_pk:
        habit = get_object_or_404(Habit, pk=habit_pk, user=request.user)
    if request.method == 'POST':
        form = HabitSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            return redirect('habit_detail', pk=session.habit.pk)
    else:
        form = HabitSessionForm(initial={'habit': habit})
    return render(request, 'dashboard/session_form.html', {
        'form': form,
        'title': 'Добавить сессию',
        'habit': habit,
    })


@login_required
def session_edit(request, pk):
    session = get_object_or_404(HabitSession, pk=pk, user=request.user)
    if request.method == 'POST':
        form = HabitSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            return redirect('habit_detail', pk=session.habit.pk)
    else:
        form = HabitSessionForm(instance=session)
    return render(request, 'dashboard/session_form.html', {
        'form': form,
        'title': 'Редактировать сессию',
        'habit': session.habit,
    })


@login_required
def session_delete(request, pk):
    session = get_object_or_404(HabitSession, pk=pk, user=request.user)
    if request.method == 'POST':
        habit_pk = session.habit.pk
        session.delete()
        return redirect('habit_detail', pk=habit_pk)
    return render(request, 'dashboard/confirm_delete.html', {
        'object': session,
        'title': 'Удалить сессию',
        'cancel_url': 'habit_detail',
        'cancel_args': [session.habit.pk],
    })


@login_required
def reports_view(request):
    user = request.user
    reports = ProductivityReport.objects.filter(user=user).order_by('-date')[:30]
    labels = [report.date.strftime('%Y-%m-%d') for report in reports][::-1]
    focus_scores = [float(report.focus_score) for report in reports][::-1]
    total_minutes = [report.total_minutes for report in reports][::-1]
    return render(request, 'dashboard/reports.html', {
        'reports': reports,
        'chart_labels': json.dumps(labels),
        'chart_focus_scores': json.dumps(focus_scores),
        'chart_total_minutes': json.dumps(total_minutes),
    })


@login_required
def dashboard_view(request):
    user = request.user
    now = timezone.localdate()
    thirty_days_ago = now - timedelta(days=30)

    habit_count = Habit.objects.filter(user=user).count()
    active_habit_count = Habit.objects.filter(user=user, is_active=True).count()
    recent_sessions = HabitSession.objects.filter(user=user).order_by('-start_time')[:10]
    reports = ProductivityReport.objects.filter(user=user, date__gte=thirty_days_ago)

    total_sessions = reports.aggregate(total=Sum('sessions_count'))['total'] or 0
    total_minutes = reports.aggregate(total=Sum('total_minutes'))['total'] or 0
    avg_focus_score = reports.aggregate(avg=Avg('focus_score'))['avg'] or 0

    context = {
        'habit_count': habit_count,
        'active_habit_count': active_habit_count,
        'recent_sessions': recent_sessions,
        'total_sessions': total_sessions,
        'total_minutes': total_minutes,
        'avg_focus_score': round(avg_focus_score, 2),
    }
    return render(request, 'dashboard/dashboard.html', context)
