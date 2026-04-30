# Generated for GDPR hardening (consent + right-to-erasure anonymisation).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="gdpr_consent",
            field=models.BooleanField(
                default=False,
                help_text="User has accepted the privacy notice. Required at registration.",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="consented_at",
            field=models.DateTimeField(
                null=True, blank=True,
                help_text="Timestamp at which gdpr_consent was set to True.",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="anonymized_at",
            field=models.DateTimeField(
                null=True, blank=True,
                help_text="If set, this account was anonymised under GDPR Art. 17.",
            ),
        ),
    ]
