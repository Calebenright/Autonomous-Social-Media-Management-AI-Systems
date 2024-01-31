from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule, name='schedule'),
    path('ad_manager/', views.ad_manager, name='ad_manager'),
    path('post_creator/', views.post_creator, name='post_creator'),
    path('brand_settings/', views.brand_settings, name='brand_settings'),
    path('library/', views.library, name='library'),
    path('callback/', views.callback, name='callback'),
    path('add_graphics/', views.add_graphics, name='add_graphics'),
    path('master_switch/', views.master_switch, name='master_switch'),
    path('all_auth/', views.all_auth, name='all_auth'),
    path('checkout/', views.checkout, name='checkout'),
    path('stripe_webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('download/', views.download, name='download'),
    path('start_chat/', views.start_chat, name='start_chat'),
    path('get_chat/', views.get_chat, name='get_chat'),
    path('clear_chat/', views.clear_chat, name='clear_chat'),
    path('unlink/', views.unlink, name='unlink'),
    path('logout_view/', views.logout_view, name='logout_view'),
    path('process_page_selection/', views.process_page_selection, name='process_page_selection'),
]
