from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('apps_calendar/', views.apps_calendar, name='apps_calendar'),
    path('comments/', views.comments, name='comments'),
    path('post_creator/', views.post_creator, name='post_creator'),
    path('upload_post/', views.upload_post, name='upload_post'),
    path('brand_settings/', views.brand_settings, name='brand_settings'),
    path('users/', views.user_list, name='user_list'),
]
