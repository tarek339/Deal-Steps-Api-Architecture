from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
import uuid


# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=100, null=True)
    lastName = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=100, null=False, unique=True, blank=False)
    password = models.CharField(max_length=128, null=False)
    street = models.CharField(max_length=100, null=True)
    houseNumber = models.CharField(max_length=100, null=True)
    zipCode = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=100, null=True)
    verificationToken = models.CharField(max_length=100, null=True)
    isVerified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.id}"

    def get_email_field_name(self):
        return f"{self.email}"

    def set_password(self, raw_password):
        """Sets the password by hashing it."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Checks the given password against the hashed password."""
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        """Override save to hash password if it's being set."""
        if self.password and not self.password.startswith("pbkdf2_sha256$"):
            self.set_password(self.password)
        super().save(*args, **kwargs)
