from django.urls import path
from django.views.generic import TemplateView
from service.views import subscribe_view
from . import views  
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('change-theme/', views.change_theme, name='change_theme'),

    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/register/', views.register_view, name='register'),

    path('habits/create_habit/', views.create_habit_view, name='habit_create'),

    path('subscribe/', subscribe_view, name='subscribe'),
    path('subscribe/success/', TemplateView.as_view(template_name='success.html'), name='subscribe-success'),
    
    path('schedule/', views.schedule, name='schedule'),
    path('habit/edit/<int:pk>/', views.habit_edit, name='habit_edit'),
    path('habit/delete/<int:pk>/', views.habit_delete, name='habit_delete'),
    path('habit/status/<int:pk>/', views.toggle_status, name='toggle_status'),
    
    path('api/tasks/', views.get_tasks, name='get_tasks'),
    path('api/tasks/add/', views.add_task, name='add_task'),
    path('api/tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('api/tasks/edit/<int:task_id>/', views.edit_task, name='edit_task'),
    
    path('api/ai-context/', views.get_ai_context, name='ai_context'),
    
    path('auth/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html'
    ), name='password_reset'),
    
    path('auth/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),
    
    path('auth/password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('auth/password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),

]
