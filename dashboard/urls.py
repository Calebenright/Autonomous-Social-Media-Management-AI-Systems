from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.calendar, name='schedule'),
    path('calendar/', views.calendar, name='calendar'),
    path('post_creator/', views.post_creator, name='post_creator'),
    path('upload_post/', views.upload_post, name='upload_post'),
    path('brand_settings/', views.brand_settings, name='brand_settings'),
    path('ad_manager/', views.ad_manager, name='ad_manager'),
]
