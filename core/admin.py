from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import User, UploadRequest

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_uploader', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('is_uploader', 'phone_number', 'profile_picture', 'bio', 'gender')}),
    )

@admin.register(UploadRequest)
class UploadRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_approved', 'processed_at')
    list_filter = ('is_approved', 'processed_at')
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        for req in queryset:
            if not req.processed_at:
                req.is_approved = True
                req.processed_at = timezone.now()
                req.save()
                # Also update user
                req.user.is_uploader = True
                req.user.save()
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        queryset.update(is_approved=False, processed_at=timezone.now())
    reject_requests.short_description = "Reject selected requests"

admin.site.register(User, CustomUserAdmin)
