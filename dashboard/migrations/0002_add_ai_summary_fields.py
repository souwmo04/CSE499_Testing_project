# Generated migration for AI summary fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='ai_summary',
            field=models.TextField(blank=True, help_text='AI-generated description of trends and insights from this snapshot'),  # noqa: E501
        ),
        migrations.AddField(
            model_name='snapshot',
            name='ai_analyzed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='snapshot',
            name='ai_analysis_error',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='title',
            field=models.CharField(default='Dashboard Snapshot', max_length=200),
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='image',
            field=models.ImageField(upload_to='snapshots/'),
        ),
        migrations.AlterModelOptions(
            name='snapshot',
            options={'ordering': ['-created_at'], 'verbose_name': 'Dashboard Snapshot', 'verbose_name_plural': 'Dashboard Snapshots'},  # noqa: E501
        ),
    ]
