from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import users.signals  # noqa
        except ImportError:
            # In case of circular imports during startup, defer signal loading
            pass