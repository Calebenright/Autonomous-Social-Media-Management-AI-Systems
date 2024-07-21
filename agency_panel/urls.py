from django.urls import path
from . import views

urlpatterns = [
    path("agency_panel/", views.agency_panel, name="agency_panel"),
    path("agency_form/", views.agency_form, name="agency_form"),
    path("agency_upload_graphic/", views.agency_upload_graphic, name="agency_upload_graphic"),
    path("agency_upload_video/", views.agency_upload_video, name="agency_upload_video"),
    path("agency_upload_ad/", views.agency_upload_ad, name="agency_upload_ad"),
    path("agency_tasks/<str:document_id>/", views.agency_tasks, name="agency_tasks"),
    path("agency_switch/<str:document_id>/", views.agency_switch, name="agency_switch"),
    path("agency_service_switch/<str:document_id>/", views.agency_service_switch, name="agency_service_switch"),
    path("agency_delete/<str:document_id>/", views.agency_delete, name="agency_delete"),
    path("agency_archive/<str:document_id>/", views.agency_archive, name="agency_archive"),
    path('add_account/<str:agency_id>/', views.add_account, name='add_account'),
]