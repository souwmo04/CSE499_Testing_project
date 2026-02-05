from django.db import models


class Snapshot(models.Model):
    """
    Model to store dashboard snapshots with AI-generated analysis.

    Each snapshot captures the dashboard state at a point in time and
    can include an AI-generated summary of the visual content.
    """
    title = models.CharField(max_length=200, default="Dashboard Snapshot")
    image = models.ImageField(upload_to='snapshots/')
    created_at = models.DateTimeField(auto_now_add=True)

    # AI-generated analysis summary (from VLM)
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated description of trends and insights from this snapshot"
    )

    # Legacy fields for backward compatibility
    gold_summary = models.TextField(blank=True)
    silver_summary = models.TextField(blank=True)
    oil_summary = models.TextField(blank=True)

    # Track if AI analysis was attempted
    ai_analyzed = models.BooleanField(default=False)
    ai_analysis_error = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Dashboard Snapshot"
        verbose_name_plural = "Dashboard Snapshots"

    def __str__(self):
        return f"Snapshot {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_image_path(self):
        """Get the full filesystem path to the image."""
        if self.image:
            return self.image.path
        return None

    def has_ai_summary(self):
        """Check if this snapshot has an AI-generated summary."""
        return bool(self.ai_summary and self.ai_summary.strip())
