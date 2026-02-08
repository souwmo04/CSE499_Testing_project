from django.apps import AppConfig
import sys

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        # Only start scheduler with runserver
        if 'runserver' not in sys.argv:
            return

        from .scheduler import start
        start()
