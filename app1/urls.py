from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('pricing/', views.pricing, name='pricing'),
    path('forgot_password/', views.forgot_password, name='forgot_password')
]