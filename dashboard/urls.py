from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule, name='schedule'),
    path('ad_manager/', views.ad_manager, name='ad_manager'),
    path('post_creator/', views.post_creator, name='post_creator'),
    path('brand_settings/', views.brand_settings, name='brand_settings'),
    path('callback/', views.callback, name='callback'),
    path('all_auth/', views.all_auth, name='all_auth'),
    path('checkout/', views.checkout, name='checkout'),
    path('stripe_webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('download/', views.download, name='download'),
]
