from django.urls import path
from . import views

app_name = 'agency'

urlpatterns = [
    path("clients", views.clients, name="clients"),
    path("upload_graphic/", views.upload_graphic, name="upload_graphic"),
    path("upload_video/", views.upload_video, name="upload_video"),
    path("upload_ad/", views.upload_ad, name="upload_ad"),
    path("elaine/", views.elaine, name="elaine"),
    path("tasks/<str:document_id>/", views.tasks, name="tasks"),
    path("service_switch/<str:document_id>/", views.service_switch, name="service_switch"),
    path("delete/<str:document_id>/", views.delete, name="delete"),
    path("archive/<str:document_id>/", views.archive, name="archive"),
    path('add_account/<str:agency_id>/', views.add_account, name='add_account'),
]