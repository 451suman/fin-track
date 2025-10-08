from django.apps import AppConfig
class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    def ready(self):
        # Import signal handlers
        from tracker import signals