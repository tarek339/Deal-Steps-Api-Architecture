from django.urls import path
from . import views

urlpatterns = [
    path("fetch_products", views.fetch_products, name="fetch_products"),
    path(
        "fetch_single_product/<uuid:productID>",
        views.fetch_single_product,
        name="fetch_single_product",
    ),
    path("add_to_cart/<uuid:id>", views.add_to_cart, name="add_to_cart"),
    path("fetch_cart/<uuid:id>", views.fetch_cart, name="fetch_cart"),
    path("remove_from_cart/<uuid:id>", views.remove_from_cart, name="remove_from_cart"),
]
