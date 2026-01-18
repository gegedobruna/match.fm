from __future__ import annotations

import time

from django.conf import settings
from django.db import transaction

from .models import MatchRequest
from .services.lastfm import (
    LastfmClient,
    LastfmError,
    LastfmRateLimitError,
    get_or_fetch_user,
    get_top_artists_with_cache,
)
from .services.scoring import compute_match


def run_match(match_id: str) -> None:
    """
    No-Celery dev mode: run match computation inline in the web request.

    Retries rate limits with simple sleep backoff (5s, 15s, 45s).
    """
    try:
        match = MatchRequest.objects.select_related("user_a", "user_b").get(uuid=match_id)
    except MatchRequest.DoesNotExist:
        return

    client = LastfmClient(api_key=settings.LASTFM_API_KEY)
    periods = ["3month", "12month", "overall"]
    limit = 300

    backoffs = [5, 15, 45]

    for attempt in range(len(backoffs) + 1):
        try:
            with transaction.atomic():
                user_a = get_or_fetch_user(client, match.user_a.username)
                user_b = get_or_fetch_user(client, match.user_b.username)

            payloads_a = {}
            payloads_b = {}
            for period in periods:
                payloads_a[period] = get_top_artists_with_cache(client, user_a, period, limit=limit)
                payloads_b[period] = get_top_artists_with_cache(client, user_b, period, limit=limit)

            result = compute_match(payloads_a, payloads_b)
            match.result = {
                "user_a": user_a.username,
                "user_b": user_b.username,
                **result,
            }
            match.status = "READY"
            match.error_message = ""
            match.save(update_fields=["result", "status", "error_message", "updated_at"])
            return

        except (LastfmRateLimitError, LastfmError) as exc:
            if attempt < len(backoffs):
                time.sleep(backoffs[attempt])
                continue

            match.status = "FAILED"
            match.error_message = str(exc)
            match.save(update_fields=["status", "error_message", "updated_at"])
            return

        except Exception as exc:  # protective catch
            match.status = "FAILED"
            match.error_message = str(exc)
            match.save(update_fields=["status", "error_message", "updated_at"])
            return
