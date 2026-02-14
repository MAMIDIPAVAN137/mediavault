from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    THEME_CHOICES = (
        ('LIGHT', 'Light'),
        ('DARK', 'Dark'),
    )

    email = models.EmailField(unique=True) 
    phone_number = models.CharField(max_length=20, blank=True, unique=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='LIGHT')
    is_uploader = models.BooleanField(default=False, help_text="Designates whether the user can upload files and create folders.")
    is_public = models.BooleanField(default=True, help_text="Designates whether the profile is visible to others.")
    is_private = models.BooleanField(default=False, help_text="If true, only followers can see content.")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_role_display(self):
        if self.is_superuser:
            return "Admin"
        if self.is_uploader:
            return "Uploader"
        return "User"

class UploadRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_requests')
    message = models.TextField(help_text="Reason for requesting upload access")
    is_approved = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request from {self.user.username}"

class ReportedProblem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_problems')
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Problem from {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"
