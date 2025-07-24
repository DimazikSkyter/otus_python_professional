from django.core.management.base import BaseCommand
from poll_app.init_seed_users import seed_users


class Command(BaseCommand):
    help = "Создание начальных пользователей"

    def handle(self, *args, **kwargs):
        seed_users()
        self.stdout.write(self.style.SUCCESS("✅ Пользователи успешно созданы"))
