from django.apps import AppConfig


class MlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml'

    def ready(self):
        import sys
        # Skip model preloading during management commands like migrate, makemigrations
        skip_commands = {'migrate', 'makemigrations', 'collectstatic', 'shell'}
        if len(sys.argv) > 1 and sys.argv[1] in skip_commands:
            return
        try:
            from ml.semantic_search import _get_model
            _get_model()
        except Exception:
            pass
