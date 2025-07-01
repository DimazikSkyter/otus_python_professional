from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "poll_app.core"

    def ready(self):
        from poll_app.init_seed_users import seed_users
