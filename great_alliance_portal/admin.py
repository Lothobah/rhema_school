from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from great_alliance_portal.models import CustomUser
# Register your models here.
#class model to keep password encrypted
class UserModel(UserAdmin):
    pass

admin.site.register(CustomUser,UserModel)
