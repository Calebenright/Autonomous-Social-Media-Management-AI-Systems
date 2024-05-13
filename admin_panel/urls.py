from django.urls import path
from . import views

urlpatterns = [
    path("feadlio_admin/", views.feadlio_admin, name="feadlio_admin"),
]