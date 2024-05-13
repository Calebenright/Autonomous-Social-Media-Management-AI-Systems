from django.urls import path
from . import views

urlpatterns = [
    path("social_media_guy/", views.social_media_guy, name="social_media_guy"),
    path("price/", views.price, name="price"),
    path("social_media_guy_success/", views.social_media_guy_success, name="social_media_guy_success"),
    path("smm_form/", views.smm_form, name="smm_form"),
    path("smm_relink/", views.smm_relink, name="smm_relink"),
    path("funnel_auth/", views.funnel_auth, name="funnel_auth"),
    path("funnel_callback/", views.funnel_callback, name="funnel_callback"),
    path("funnel_unlink/", views.funnel_unlink, name="funnel_unlink"),
    path("funnel_process_page_selection/", views.funnel_process_page_selection, name="funnel_process_page_selection"),
]