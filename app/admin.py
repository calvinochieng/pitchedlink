from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Pitch, Category, PitchAnalytics, UserProfile, Claim, TweetBatch, ReplyOpportunity

@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    # Search configuration
    search_fields = [
        'name',
        'title',
        'description',
        'content',
        'url',
        'source',
        'user__username',
        'user__email',
        'category__name',
        'tags',
    ]
    
    # List display configuration
    list_display = (
        'name',
        'title',
        'user',
        'category',
        'is_featured',
        'is_launched',
        'rank',
        'created_at',
        'view_analytics'
    )
    
    # List filter configuration
    list_filter = (
        'is_featured',
        'is_launched',
        'claimed',
        'category',
        'created_at',
    )
    
    # Fieldsets for add/edit form
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'title', 'description', 'content', 'category', 'tags')
        }),
        ('Media & URLs', {
            'fields': ('icon_url', 'banner_url', 'url', 'source')
        }),
        ('Status & Metadata', {
            'fields': ('is_featured', 'is_launched', 'launch_date', 'claimed', 'rank')
        }),
        ('JSON Data', {
            'classes': ('collapse',),
            'fields': ('seo_data', 'pitch_data', 'meta_data', 'total_engagement'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    # Readonly fields
    readonly_fields = ('created_at', 'updated_at')
    
    # Date hierarchy
    date_hierarchy = 'created_at'
    
    # Custom actions
    actions = ['mark_as_featured', 'mark_as_launched']
    
    def view_analytics(self, obj):
        url = reverse('admin:app_pitchanalytics_change', args=[obj.analytics.id]) if hasattr(obj, 'analytics') else '#'
        return format_html('<a href="{}">View Analytics</a>', url) if hasattr(obj, 'analytics') else 'No Analytics'
    view_analytics.short_description = 'Analytics'
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'Marked {updated} pitches as featured.')
    mark_as_featured.short_description = 'Mark selected pitches as featured'
    
    def mark_as_launched(self, request, queryset):
        updated = queryset.update(is_launched=True)
        self.message_user(request, f'Marked {updated} pitches as launched.')
    mark_as_launched.short_description = 'Mark selected pitches as launched'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(PitchAnalytics)
class PitchAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('pitch', 'views_total', 'clicks_total', 'last_view', 'last_click')
    list_filter = ('last_view', 'last_click')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('pitch__name', 'pitch__title')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'x_handle', 'onboarding_complete', 'created_at')
    list_filter = ('onboarding_complete', 'created_at')
    search_fields = ('user__username', 'user__email', 'x_handle')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('user', 'pitch', 'status', 'claimed_at', 'verified_at')
    list_filter = ('status', 'claimed_at', 'verified_at')
    search_fields = ('user__username', 'user__email', 'pitch__name', 'pitch__title')
    readonly_fields = ('claimed_at', 'verified_at')

#------Tweet Batch Admin------#

@admin.register(TweetBatch)
class TweetBatchAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "count_imported")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {
            "fields": ("name", "raw_urls", "created_at"),
            "description": "Paste your Tweet URLs (one per line) below."
        }),
    )

    def count_imported(self, obj):
        # Count how many opportunities exist with urls from this batch
        lines = [u.strip() for u in obj.raw_urls.splitlines() if u.strip()]
        return ReplyOpportunity.objects.filter(url__in=lines).count()
    count_imported.short_description = "Tweets Imported"


@admin.register(ReplyOpportunity)
class ReplyOpportunityAdmin(admin.ModelAdmin):
    list_display = ("url", "imported_at")
    search_fields = ("url","content")
    exclude = ("content","imported_at")


