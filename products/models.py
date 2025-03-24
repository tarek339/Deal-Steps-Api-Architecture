from django.db import models
from customer.models import *
import uuid


# Create your models here.
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shopName = models.CharField(max_length=100, null=True, blank=False)
    brand = models.CharField(max_length=100, null=True, blank=False)
    description = models.CharField(max_length=100, null=True, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    imageUrl = models.CharField(max_length=500, null=True, blank=False)

    def __str__(self):
        return f"{self.id}"


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="carts", null=True, blank=True
    )

    def __str__(self):
        return f"{self.customer.firstName} {self.customer.lastName} {self.id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    total = models.DecimalField(default=0, max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.cart.customer.firstName} {self.cart.customer.lastName} {self.product.brand}"

    def calc_total(self):
        self.total = self.quantity * self.product.price
        return self.total

    def save(self, *args, **kwargs):
        self.calc_total()
        super().save(*args, **kwargs)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="order", null=True, blank=True
    )

    def __str__(self):
        return f"{self.id} {self.customer.id}"
