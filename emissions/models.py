from django.db import models
from django.contrib.auth.models import User


class Organization(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.organization}"

class UploadBatch(models.Model):

    SOURCE_CHOICES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE,
        null=True, blank=True
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    suspicious_rows = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.source} — {self.filename}"


class EmissionRecord(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('suspicious', 'Suspicious'),
        ('failed', 'Failed Validation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    SCOPE_CHOICES = [
        ('scope_1', 'Scope 1'),
        ('scope_2', 'Scope 2'),
        ('scope_3', 'Scope 3'),
    ]

    batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE)
    source_row_number = models.IntegerField()
    source = models.CharField(max_length=10)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    date = models.DateField(null=True, blank=True)
    description = models.TextField()
    quantity = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    validation_errors = models.JSONField(default=list)
    analysis_flags = models.JSONField(default=list)
    transformations = models.JSONField(default=list)
    raw_data = models.JSONField()
    approved_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_records'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} row {self.source_row_number} — {self.status}"