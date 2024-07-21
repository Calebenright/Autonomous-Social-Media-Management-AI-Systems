from django.urls import path
from . import views

urlpatterns = [
    path("feadlio_admin/", views.feadlio_admin, name="feadlio_admin"),
    path("feadlio_crm/", views.feadlio_crm, name="feadlio_crm"),
    path("admin_links/", views.admin_links, name="admin_links"),
    path("send_crm_email/", views.send_crm_email, name="send_crm_email"),
    path('update_priority/', views.update_priority, name='update_priority'),
    path('delete_user/', views.delete_user, name='delete_user'),
]