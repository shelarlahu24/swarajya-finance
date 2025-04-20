from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    ROLE_CHOICES=(
        ('admin','Admin'),
        ('agent','Agent'),
    )

    user=models.OneToOneField(User,on_delete=models.CASCADE)
    role=models.CharField(max_length=25,choices=ROLE_CHOICES)
    phone=models.CharField(max_length=10)
    address=models.CharField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"