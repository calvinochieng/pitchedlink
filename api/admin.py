# admin.py (optional)
from django.contrib import admin
from .models import APIKey

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'prefix', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['key_hash', 'prefix', 'created_at', 'last_used']
    
    def prefix(self, obj):
        return f"{obj.prefix}..."


