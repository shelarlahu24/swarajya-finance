from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import CustomUser
# Register your models here.
admin.site.unregister(Group)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('role','phone', 'address')}),
    )

admin.site.register(CustomUser,CustomUserAdmin)