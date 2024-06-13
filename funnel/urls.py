from django.urls import path
from . import views

urlpatterns = [
    path("social_media_guy_calendly/", views.social_media_guy_calendly, name="social_media_guy_calendly"),
    path("social_media_guy_form/", views.social_media_guy_form, name="social_media_guy_form"),
    path("social_media_guy/", views.social_media_guy, name="social_media_guy"),
    path("beta_signup/", views.beta_signup, name="beta_signup"),
    path("price_5/", views.price_5, name="price_5"),
    path("social_media_guy_success/", views.social_media_guy_success, name="social_media_guy_success"),
    path("free_smm/", views.free_smm, name="free_smm"),
    path("free_photography/", views.free_photography, name="free_photography"),
    path("free_airbnb_photography/", views.free_airbnb_photography, name="free_airbnb_photography"),
    path("getting_started/", views.getting_started, name="getting_started"),
    path("smm_form/", views.smm_form, name="smm_form"),
    path("smm_relink/", views.smm_relink, name="smm_relink"),
    path("funnel_auth/", views.funnel_auth, name="funnel_auth"),
    path("funnel_callback/", views.funnel_callback, name="funnel_callback"),
    path("funnel_unlink/", views.funnel_unlink, name="funnel_unlink"),
    path("funnel_process_page_selection/", views.funnel_process_page_selection, name="funnel_process_page_selection"),
]