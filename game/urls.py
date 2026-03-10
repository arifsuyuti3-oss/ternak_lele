from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('game/register/', views.register_view, name='register'),
    path('game/login/', views.login_view, name='login'),
    path('game/logout/', views.logout_view, name='logout'),
    path('game/dashboard/', views.dashboard, name='dashboard'),
    path('game/beli-benih/', views.beli_benih, name='beli_benih'),
    path('game/beri-pakan/', views.beri_pakan, name='beri_pakan'),
    path('game/jual-lele/', views.jual_lele, name='jual_lele'),
    path('game/history/', views.history, name='history'),
]
