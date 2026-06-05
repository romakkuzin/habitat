from django.urls import path
from . import views

app_name = 'dashboard_admin'

urlpatterns = [
    path('', views.admin_index, name='index'),
    path('users/', views.admin_users, name='users'),
    path('habits/', views.admin_habits, name='habits'),
    path('sessions/', views.admin_sessions, name='sessions'),
]
