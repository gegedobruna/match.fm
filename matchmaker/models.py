import uuid
from django.db import models
from django.utils import timezone


PERIOD_CHOICES = [
    ("3month", "Last 3 months"),
    ("12month", "Last 12 months"),
    ("overall", "Overall"),
]

STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("READY", "Ready"),
    ("FAILED", "Failed"),
]


class LastfmUser(models.Model):
    username = models.CharField(max_length=50, unique=True, db_index=True)
    playcount = models.BigIntegerField(null=True, blank=True)
    realname = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.username


class TopArtistSnapshot(models.Model):
    user = models.ForeignKey(
        LastfmUser, on_delete=models.CASCADE, related_name="artist_snapshots"
    )
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    limit = models.PositiveIntegerField()
    payload = models.JSONField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "period", "limit"],
                name="unique_snapshot_per_user_period_limit",
            )
        ]

    def is_fresh(self, ttl_hours: int = 12) -> bool:
        if not self.fetched_at:
            return False
        return self.fetched_at >= timezone.now() - timezone.timedelta(hours=ttl_hours)

    def __str__(self) -> str:
        return f"{self.user.username} {self.period} (limit {self.limit})"


class MatchRequest(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_a = models.ForeignKey(
        LastfmUser, related_name="matches_as_a", on_delete=models.CASCADE
    )
    user_b = models.ForeignKey(
        LastfmUser, related_name="matches_as_b", on_delete=models.CASCADE
    )
    period_mode = models.CharField(max_length=50, default="weighted")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    error_message = models.TextField(blank=True)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user_a.username} vs {self.user_b.username}"
