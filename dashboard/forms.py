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
    email = forms.EmailField(required=True, label='Email')

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
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class HabitSessionForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = HabitSession
        fields = ['habit', 'start_time', 'end_time', 'interruptions', 'notes']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
