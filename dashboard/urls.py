from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import TagViewSet, HabitViewSet, HabitSessionViewSet, ProductivityReportViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'habits', HabitViewSet, basename='habit')
router.register(r'sessions', HabitSessionViewSet, basename='session')
router.register(r'reports', ProductivityReportViewSet, basename='report')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
