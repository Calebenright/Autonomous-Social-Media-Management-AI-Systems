from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('login/', views.login, name='login'),
    path("logout/", views.logout, name="logout"),
    path('pricing/', views.pricing, name='pricing'),
    path('signup/', views.signup, name='signup'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('change_email/', views.change_email, name='change_email'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('terms_of_service/', views.terms_of_service, name='terms_of_service'),
    path('contact/', views.contact, name='contact'),
    path('robots.txt', views.robots_txt, name='robots.txt'),
    path('graphic_builder/', views.graphic_builder, name='graphic_builder'),
    path('articles/', views.get_articles, name='articles'),
    path('articles/<slug:article_slug>/', views.article_detail, name='article_detail'),
    path('iframe-content/', views.iframe_content, name='iframe_content'),
]