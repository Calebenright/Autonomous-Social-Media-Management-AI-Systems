from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path("products/", views.products, name="products"),
    path("thank-you/", views.thank_you, name="thank-you"),
    path("item1/", views.item1, name="item1"),
    path("item2/", views.item2, name="item2"),
]