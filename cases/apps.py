from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cases'
    
    # def ready(self):
    #     # Import signals here so that they are registered
    #     import cases.signals