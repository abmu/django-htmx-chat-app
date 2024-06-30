from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class MyUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
        ('{Section name}', {'fields': ()}),
    )

admin.site.register(User, MyUserAdmin)