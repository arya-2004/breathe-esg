from django.contrib import admin
from .models import UploadBatch, EmissionRecord, Organization, UserProfile

admin.site.register(UploadBatch)
admin.site.register(EmissionRecord)
admin.site.register(Organization)
admin.site.register(UserProfile)