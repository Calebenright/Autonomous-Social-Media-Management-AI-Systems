from django.urls import path
from . import views

urlpatterns = [
    path("my_feadlio/", views.my_feadlio, name="my_feadlio"),
    path("my_account/", views.my_account, name="my_account"),
    path("my_account_relink/", views.my_account_relink, name="my_account_relink"),
    path("my_feadlio_success/", views.my_feadlio_success, name="my_feadlio_success"),
    path("my_account_stripe_redirect/", views.my_account_stripe_redirect, name="my_account_stripe_redirect"),
    path("service_dashboard/", views.service_dashboard, name="service_dashboard"),
    path("service_brand_settings/", views.service_brand_settings, name="service_brand_settings"),
    path("service_calendar/", views.service_calendar, name="service_calendar"),
    path("service_checkout/", views.service_checkout, name="service_checkout"),
    path("service_auth/", views.service_auth, name="service_auth"),
    path("service_callback/", views.service_callback, name="service_callback"),
    path("service_unlink/", views.service_unlink, name="service_unlink"),
    path("service_process_page_selection/", views.service_process_page_selection, name="service_process_page_selection"),
]