from django.urls import path
from . import views

urlpatterns = [
    path("my_feadlio/", views.my_feadlio, name="my_feadlio"),
    path("my_feadlio_success/", views.my_feadlio_success, name="my_feadlio_success"),
    path("service_dashboard_ftue/", views.service_dashboard_ftue, name="service_dashboard_ftue"),
    path("service_dashboard/", views.service_dashboard, name="service_dashboard"),
    path("service_graphic_designer/", views.service_graphic_designer, name="service_graphic_designer"),
    path("service_video_editor/", views.service_video_editor, name="service_video_editor"),
    path("service_advertising_specialist/", views.service_advertising_specialist, name="service_advertising_specialist"),
    path("service_brand_settings/", views.service_brand_settings, name="service_brand_settings"),
    path("service_calendar/", views.service_calendar, name="service_calendar"),
    path("service_library/", views.service_library, name="service_library"),
    path("service_ad_checkout/", views.service_ad_checkout, name="service_ad_checkout"),
    path("service_business_checkout/", views.service_business_checkout, name="service_business_checkout"),
    path("service_checkout/", views.service_checkout, name="service_checkout"),
    path("service_auth/", views.service_auth, name="service_auth"),
    path("service_callback/", views.service_callback, name="service_callback"),
    path("service_download/", views.service_download, name="service_download"),
    path("service_unlink/", views.service_unlink, name="service_unlink"),
    path("service_submit_brief/", views.service_submit_brief, name="service_submit_brief"),
    path("service_generate_signed_url/", views.service_generate_signed_url, name="service_generate_signed_url"),
    path("service_make_file_public/", views.service_make_file_public, name="service_make_file_public"),
    path("service_process_page_selection/", views.service_process_page_selection, name="service_process_page_selection"),
]