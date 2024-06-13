from django.urls import path
from . import views

urlpatterns = [
    path("agency_panel/", views.agency_panel, name="agency_panel"),
    path("agency_form/", views.agency_form, name="agency_form"),
    path("agency_switch/<str:document_id>/", views.agency_switch, name="agency_switch"),
    path("agency_delete/<str:document_id>/", views.agency_delete, name="agency_delete"),
    path('add_account/<str:agency_id>/', views.add_account, name='add_account'),
]