"""Create or reset a superuser non-interactively.

Usage:
    python manage.py make_admin EMAIL PASSWORD [--username NAME]

Examples:
    python manage.py make_admin admin@local admin
    python manage.py make_admin koen@example.com s3cret-passw0rd! --username koen

Bypasses AUTH_PASSWORD_VALIDATORS so short dev passwords like "admin" still
work; do NOT use this for real users in production.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or reset a superuser by email + password (non-interactive)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("email", help="Email address (login field).")
        parser.add_argument("password", help="Password to set.")
        parser.add_argument(
            "--username", default=None,
            help="Optional username. Defaults to the part of the email before @.",
        )

    def handle(self, *_args, **options) -> None:
        User = get_user_model()
        email = options["email"].strip().lower()
        password = options["password"]
        username = options["username"] or email.split("@", 1)[0]

        user, created = User.objects.update_or_create(
            email=email,
            defaults={
                "username": username,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.set_password(password)
        # Mark dev admins as having consented so they can log in cleanly.
        if hasattr(user, "gdpr_consent"):
            user.gdpr_consent = True
            from django.utils import timezone
            user.consented_at = timezone.now()
        user.save()

        verb = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(
            f"Superuser {verb}: email={email}  username={username}",
        ))
        self.stdout.write("Log in at /admin/ with that email + the password you just set.")
