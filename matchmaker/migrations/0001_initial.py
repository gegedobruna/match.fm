from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LastfmUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(db_index=True, max_length=50, unique=True)),
                ("playcount", models.BigIntegerField(blank=True, null=True)),
                ("realname", models.CharField(blank=True, max_length=255)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("avatar_url", models.URLField(blank=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="MatchRequest",
            fields=[
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("period_mode", models.CharField(default="weighted", max_length=50)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("READY", "Ready"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("error_message", models.TextField(blank=True)),
                ("result", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user_a", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="matches_as_a", to="matchmaker.lastfmuser")),
                ("user_b", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="matches_as_b", to="matchmaker.lastfmuser")),
            ],
        ),
        migrations.CreateModel(
            name="TopArtistSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period", models.CharField(choices=[("3month", "Last 3 months"), ("12month", "Last 12 months"), ("overall", "Overall")], max_length=20)),
                ("limit", models.PositiveIntegerField()),
                ("payload", models.JSONField()),
                ("fetched_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="artist_snapshots", to="matchmaker.lastfmuser")),
            ],
        ),
        migrations.AddConstraint(
            model_name="topartistsnapshot",
            constraint=models.UniqueConstraint(fields=("user", "period", "limit"), name="unique_snapshot_per_user_period_limit"),
        ),
    ]
