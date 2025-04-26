from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Property,PropertyImage,Application,Notification,Payment,PropertyReview

# Register your models here.

admin.site.register(User, UserAdmin)
admin.site.register(Property)
admin.site.register(PropertyImage)
admin.site.register(Application)
admin.site.register(Notification)
admin.site.register(Payment)
admin.site.register(PropertyReview)