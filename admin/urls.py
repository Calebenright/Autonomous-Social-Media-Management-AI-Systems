from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    path("database/", views.database, name="database"),
    path("crm/", views.crm, name="crm"),
    path("links/", views.links, name="links"),
    path("send_crm_email/", views.send_crm_email, name="send_crm_email"),
    path('update_priority/', views.update_priority, name='update_priority'),
    path('delete_user/', views.delete_user, name='delete_user'),
]