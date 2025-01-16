from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('start_chat/', views.start_chat, name='start_chat'),
    path('get_chat/', views.get_chat, name='get_chat'),
    path('clear_chat/', views.clear_chat, name='clear_chat'),
    path('add_graphics/', views.add_graphics, name='add_graphics'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('tiktok-callback/', views.tiktok_callback, name='tiktok_callback'),
    path("callback/", views.callback, name="callback"),

    # API #
    path('stripe_webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('create-checkout-session/<str:plan>/', views.create_checkout_session, name='create_checkout_session'),
    path('elaine_generate_post/', views.elaine_generate_post, name='elaine_generate_post'),
    path('add_graphics_api/', views.add_graphics_api, name='add_graphics_api'),
    path('elaine_email/', views.elaine_email, name='elaine_email'),
    path('elaine_functions/', views.elaine_functions, name='elaine_functions'),
    path('automated_email/', views.automated_email, name='automated_email'),
    path('feadlio_automatic_manager_task_creator/', views.feadlio_automatic_manager_task_creator, name='feadlio_automatic_manager_task_creator'),
    path('master_automatic_manager_task_creator/', views.master_automatic_manager_task_creator, name='master_automatic_manager_task_creator'),
    path('cron_delete_images_in_gcp_folder/', views.cron_delete_images_in_gcp_folder, name='cron_delete_images_in_gcp_folder'),
    path('cron_inactive_users/', views.cron_inactive_users, name='cron_inactive_users'),
    path('cron_reset_monthly_limits/', views.cron_reset_monthly_limits, name='cron_reset_monthly_limits'),
    path('cron_auto_add_article/', views.cron_auto_add_article, name='cron_auto_add_article'),    
    path('reset_leaderboard/', views.reset_leaderboard, name='reset_leaderboard'),    
]
