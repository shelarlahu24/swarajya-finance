from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Customer(models.Model):
    full_name=models.CharField(max_length=100)
    phone=models.CharField(unique=True, max_length=10)
    email=models.CharField(max_length=255,blank=True,null=True)
    address=models.TextField()
    aadhar_number=models.CharField(max_length=12,unique=True)
    pan_number=models.CharField(max_length=10,unique=True)
    agent=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='assigned_customers')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
