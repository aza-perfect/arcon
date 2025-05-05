from django.apps import AppConfig

class ProductionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'production'
    verbose_name = 'Proizvodstvo'

    def ready(self):
        # локальный импорт signals только после готовности registry
        from . import signals
