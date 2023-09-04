from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule, name='schedule'),
    path('post_creator/', views.post_creator, name='post_creator'),
    path('brand_settings/', views.brand_settings, name='brand_settings'),
]
