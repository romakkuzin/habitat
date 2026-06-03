from django.contrib import admin
from .models import Habit, HabitSession, Tag, ProductivityReport


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'target_frequency', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['title', 'user__username']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'description', 'is_active')
        }),
        ('Параметры', {
            'fields': ('target_frequency', 'tags')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HabitSession)
class HabitSessionAdmin(admin.ModelAdmin):
    list_display = ['habit', 'user', 'start_time', 'duration_minutes', 'interruptions', 'created_at']
    list_filter = ['user', 'created_at', 'habit__user']
    search_fields = ['habit__title', 'user__username', 'notes']
    readonly_fields = ['duration_minutes', 'created_at']

    fieldsets = (
        ('Информация о сессии', {
            'fields': ('habit', 'user')
        }),
        ('Время и длительность', {
            'fields': ('start_time', 'end_time', 'duration_minutes')
        }),
        ('Качество', {
            'fields': ('interruptions', 'notes')
        }),
        ('Служебные данные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductivityReport)
class ProductivityReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_minutes', 'sessions_count', 'focus_score', 'updated_at']
    list_filter = ['user', 'date']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Идентификация', {
            'fields': ('user', 'date')
        }),
        ('Агрегированные данные', {
            'fields': ('total_minutes', 'sessions_count', 'avg_session_length', 'avg_interruptions')
        }),
        ('Метрики продуктивности', {
            'fields': ('focus_score',)
        }),
        ('Служебные данные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
