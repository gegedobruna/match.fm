from django.contrib import admin

from .models import LastfmUser, MatchRequest, TopArtistSnapshot


@admin.register(LastfmUser)
class LastfmUserAdmin(admin.ModelAdmin):
    list_display = ("username", "playcount", "country", "last_synced_at")
    search_fields = ("username", "realname", "country")


@admin.register(TopArtistSnapshot)
class TopArtistSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "period", "limit", "fetched_at")
    list_filter = ("period",)
    search_fields = ("user__username",)


@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user_a", "user_b", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user_a__username", "user_b__username")
