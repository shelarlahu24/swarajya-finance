from django.contrib import admin
from .models import Profile
# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    list_display=['user','role','phone']
    list_filter=['role']
    search_fields=['user__username','phone']

admin.site.register(Profile,ProfileAdmin)