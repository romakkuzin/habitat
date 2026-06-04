from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Habit, HabitSession

User = get_user_model()


class TailwindFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = 'mt-2 block w-full rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200'
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {base_classes}'.strip()


class RegistrationForm(TailwindFormMixin, UserCreationForm):
    username = forms.CharField(label='Имя пользователя')
    email = forms.EmailField(required=True, label='Email')
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email


class LoginForm(TailwindFormMixin, AuthenticationForm):
    username = forms.CharField(label='Имя пользователя')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class HabitForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['title', 'description', 'target_frequency', 'is_active', 'tags']
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'target_frequency': 'Цель в неделю',
            'is_active': 'Активна',
            'tags': 'Теги',
        }
        help_texts = {
            'target_frequency': 'Желательное количество раз в неделю',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class HabitSessionForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = HabitSession
        fields = ['habit', 'start_time', 'end_time', 'interruptions', 'notes']
        labels = {
            'habit': 'Привычка',
            'start_time': 'Начало',
            'end_time': 'Окончание',
            'interruptions': 'Прерывания',
            'notes': 'Заметки',
        }
        help_texts = {
            'interruptions': 'Сколько раз вы прерывались во время сессии',
            'notes': 'Дополнительные заметки о сессии',
        }
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
