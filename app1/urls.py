from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('pricing/', views.pricing, name='pricing'),
    path('about/', views.about, name='about'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
]