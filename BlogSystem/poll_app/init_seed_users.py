import os

import django


def seed_users():
    from django.contrib.auth.models import User

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@example.com", "adminpass")
    if not User.objects.filter(username="user1").exists():
        User.objects.create_user("user1", "user1@example.com", "userpass")
    if not User.objects.filter(username="user2").exists():
        User.objects.create_user("user2", "user2@example.com", "userpass")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poll_app.settings")
    django.setup()

    seed_users()
