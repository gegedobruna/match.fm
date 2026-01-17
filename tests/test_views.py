from django.test import TestCase
from django.urls import reverse

from matchmaker.models import LastfmUser, MatchRequest


class MatchDetailViewTests(TestCase):
    def test_ready_match_renders(self):
        user_a = LastfmUser.objects.create(username="alice")
        user_b = LastfmUser.objects.create(username="bob")
        result_payload = {
            "final_score": 88.8,
            "scores": {"3month": 0.8, "12month": 0.9, "overall": 1.0},
            "overlap": [{"artist": "Shared", "a_weight": 1.1, "b_weight": 1.2, "combined": 2.3}],
            "recs_for_a": [{"artist": "From Bob", "weight": 1.0}],
            "recs_for_b": [{"artist": "From Alice", "weight": 1.0}],
        }
        match = MatchRequest.objects.create(
            user_a=user_a, user_b=user_b, status="READY", result=result_payload
        )

        url = reverse("match_detail", args=[match.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shared obsessions")
        self.assertContains(response, "88.8")
