from __future__ import annotations

import math
import time
from typing import Dict, List, Optional

import requests
from django.utils import timezone

from matchmaker.models import LastfmUser, TopArtistSnapshot

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"


class LastfmError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class LastfmRateLimitError(LastfmError):
    pass


def artist_identifier(artist: Dict) -> str:
    mbid = artist.get("mbid")
    if mbid:
        return mbid
    return artist.get("name", "").lower()


class LastfmClient:
    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
        self.api_key = api_key
        self.session = session or requests.Session()

    def _request(self, params: Dict) -> Dict:
        params = {**params, "api_key": self.api_key, "format": "json"}
        response = self.session.get(LASTFM_BASE_URL, params=params, timeout=15)
        if response.status_code == 429:
            raise LastfmRateLimitError(429, "Rate limited by Last.fm")
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            code = data.get("error", -1)
            message = data.get("message", "Unknown error")
            if code == 429:
                raise LastfmRateLimitError(code, message)
            raise LastfmError(code, message)
        return data

    def get_user_info(self, username: str) -> Dict:
        return self._request({"method": "user.getInfo", "user": username}).get("user", {})

    def get_top_artists(self, username: str, period: str, limit: int = 300) -> List[Dict]:
        data = self._request(
            {"method": "user.getTopArtists", "user": username, "period": period, "limit": limit}
        )
        artists = data.get("topartists", {}).get("artist", [])
        trimmed = []
        for artist in artists:
            trimmed.append(
                {
                    "name": artist.get("name"),
                    "mbid": artist.get("mbid"),
                    "playcount": int(artist.get("playcount", 0)),
                    "url": artist.get("url"),
                }
            )
        return trimmed


def get_or_fetch_user(client: LastfmClient, username: str, ttl_hours: int = 24) -> LastfmUser:
    user, _ = LastfmUser.objects.get_or_create(username=username)
    if user.last_synced_at and user.last_synced_at >= timezone.now() - timezone.timedelta(
        hours=ttl_hours
    ):
        return user

    info = client.get_user_info(username)
    user.playcount = int(info.get("playcount") or 0)
    user.realname = info.get("realname") or ""
    user.country = info.get("country") or ""
    images = info.get("image") or []
    avatar = ""
    if images:
        # pick the last (largest) image if available
        avatar = images[-1].get("#text") or ""
    user.avatar_url = avatar
    user.last_synced_at = timezone.now()
    user.save()
    return user


def get_top_artists_with_cache(
    client: LastfmClient, user: LastfmUser, period: str, limit: int = 300, ttl_hours: int = 12
) -> List[Dict]:
    try:
        snapshot = TopArtistSnapshot.objects.get(user=user, period=period, limit=limit)
        if snapshot.is_fresh(ttl_hours=ttl_hours):
            return snapshot.payload
    except TopArtistSnapshot.DoesNotExist:
        snapshot = None

    payload = client.get_top_artists(user.username, period=period, limit=limit)
    TopArtistSnapshot.objects.update_or_create(
        user=user,
        period=period,
        limit=limit,
        defaults={"payload": payload, "fetched_at": timezone.now()},
    )
    return payload


def retryable_call(fn, max_attempts: int = 3, base_delay: float = 5.0):
    attempt = 0
    while True:
        try:
            return fn()
        except LastfmRateLimitError:
            attempt += 1
            if attempt >= max_attempts:
                raise
            delay = base_delay * math.pow(3, attempt - 1)
            time.sleep(delay)
        except LastfmError:
            attempt += 1
            if attempt >= max_attempts:
                raise
            delay = base_delay * math.pow(3, attempt - 1)
            time.sleep(delay)
