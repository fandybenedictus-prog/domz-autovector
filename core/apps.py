"""
Core App Configuration
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import signals agar terdaftar saat app siap
        import core.signals  # noqa: F401
