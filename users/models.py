from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES=(
        ('admin','Admin'),
        ('agent','Agent'),
    )

    role=models.CharField(max_length=25,choices=ROLE_CHOICES)
    phone=models.CharField(max_length=10)
    address=models.CharField(max_length=255,blank=True)

    def __str__(self):
        return f"{self.username}"