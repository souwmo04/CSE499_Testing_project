from django.db import models

class Snapshot(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='snapshots/')
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional metadata
    gold_summary = models.TextField(blank=True)
    silver_summary = models.TextField(blank=True)
    oil_summary = models.TextField(blank=True)

    def __str__(self):
        return f"Snapshot {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
