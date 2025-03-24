from django.urls import path
from . import views

urlpatterns = [
    path("register_new_customer", views.sign_up_customer, name="register_new_customer"),
    path("sign_in_customer", views.sign_in_customer, name="sign_in_customer"),
    path("verify_email", views.verify_email, name="verify_email"),
    path(
        "get_customer_profile", views.get_customer_profile, name="get_customer_profile"
    ),
    path(
        "edit_customer_profile/<uuid:id>",
        views.edit_costumer_profile,
        name="edit_customer_profile",
    ),
    path(
        "delete_customer/<uuid:id>",
        views.delete_customer,
        name="delete_customer",
    ),
    path(
        "change_costumers_password/<uuid:id>",
        views.change_constumers_password,
        name="change_costumers_password",
    ),
    path(
        "change_costumers_email/<uuid:id>",
        views.change_costumers_email,
        name="change_costumers_email",
    ),
]
