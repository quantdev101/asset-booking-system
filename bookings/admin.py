from django.contrib import admin
from .models import Resource, Booking, StudentProfile

admin.site.register(Resource)
admin.site.register(Booking)
admin.site.register(StudentProfile)