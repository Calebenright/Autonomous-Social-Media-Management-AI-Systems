from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('pricing/', views.pricing, name='pricing'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('login_redirect/', views.login_redirect, name='login_redirect'),
    path('google_signin/', views.google_sign_in, name='google_sign_in'),
    path('google_auth_callback/', views.google_auth_callback, name='google_auth_callback'),
    path('facebook_signin/', views.facebook_sign_in, name='facebook_sign_in'),
    path('facebook_auth_callback/', views.facebook_auth_callback, name='facebook_auth_callback'),
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
    path('update_is_provider/', views.update_is_provider, name='update_is_provider'),
]