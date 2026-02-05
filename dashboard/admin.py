from django.contrib import admin
from django.utils.html import format_html
from .models import Snapshot


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    """
    Admin configuration for Snapshot model.
    Provides a clean interface for viewing and managing dashboard snapshots.
    """

    list_display = [
        'id',
        'title',
        'created_at',
        'ai_analyzed',
        'has_summary',
        'image_thumbnail'
    ]

    list_filter = ['ai_analyzed', 'created_at']
    search_fields = ['title', 'ai_summary']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'image_preview', 'ai_analyzed']

    fieldsets = (
        ('Snapshot Info', {
            'fields': ('title', 'image', 'image_preview', 'created_at')
        }),
        ('AI Analysis', {
            'fields': ('ai_summary', 'ai_analyzed', 'ai_analysis_error'),
            'classes': ('collapse',)
        }),
        ('Legacy Fields', {
            'fields': ('gold_summary', 'silver_summary', 'oil_summary'),
            'classes': ('collapse',)
        }),
    )

    def image_thumbnail(self, obj):
        """Display small thumbnail in list view."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 60px; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    image_thumbnail.short_description = "Preview"

    def image_preview(self, obj):
        """Display larger preview in detail view."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return "No image uploaded"
    image_preview.short_description = "Image Preview"

    def has_summary(self, obj):
        """Show if snapshot has AI summary."""
        if obj.ai_summary:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: gray;">No</span>')
    has_summary.short_description = "AI Summary"
