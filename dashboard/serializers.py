from rest_framework import serializers
from .models import Habit, HabitSession, Tag, ProductivityReport


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['id', 'created_at']


class HabitSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        write_only=True,
        many=True,
        source='tags'
    )

    class Meta:
        model = Habit
        fields = ['id', 'title', 'description', 'target_frequency', 'is_active', 'tags', 'tag_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_target_frequency(self, value):
        if value < 0:
            raise serializers.ValidationError('Целевая частота не может быть отрицательной')
        return value


class HabitSessionSerializer(serializers.ModelSerializer):
    habit_title = serializers.CharField(source='habit.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = HabitSession
        fields = ['id', 'habit', 'habit_title', 'user', 'user_username', 'start_time', 'end_time', 'duration_minutes', 'interruptions', 'notes', 'created_at']
        read_only_fields = ['id', 'duration_minutes', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        habit = data.get('habit')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if habit and request and habit.user != request.user:
            raise serializers.ValidationError('Вы не можете создавать или изменять сессию для этой привычки.')
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError('Время окончания должно быть позже времени начала')
        if data.get('interruptions', 0) < 0:
            raise serializers.ValidationError('Количество прерываний не может быть отрицательным')
        return data


class ProductivityReportSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductivityReport
        fields = ['id', 'user', 'user_username', 'date', 'total_minutes', 'sessions_count', 'avg_session_length', 'avg_interruptions', 'focus_score', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class HabitDetailSerializer(HabitSerializer):
    """Расширенный сериализатор привычки с информацией о сессиях"""
    sessions = HabitSessionSerializer(many=True, read_only=True)

    class Meta:
        model = Habit
        fields = ['id', 'title', 'description', 'target_frequency', 'is_active', 'tags', 'tag_ids', 'sessions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'sessions']
