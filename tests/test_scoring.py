import math

from django.test import SimpleTestCase

from matchmaker.services.scoring import compute_match, cosine_similarity


class ScoringTests(SimpleTestCase):
    def test_cosine_similarity_basic(self):
        vec_a = {"x": 1.0, "y": 2.0}
        vec_b = {"x": 1.0, "y": 2.0}
        self.assertTrue(math.isclose(cosine_similarity(vec_a, vec_b), 1.0))

        vec_c = {"x": 1.0}
        vec_d = {"y": 1.0}
        self.assertEqual(cosine_similarity(vec_c, vec_d), 0.0)

    def test_compute_match_weights_and_blend(self):
        payload_a = {
            "overall": [{"name": "Artist1", "mbid": "", "playcount": 100}],
            "3month": [{"name": "Artist1", "mbid": "", "playcount": 50}],
            "12month": [{"name": "Artist2", "mbid": "", "playcount": 20}],
        }
        payload_b = {
            "overall": [{"name": "Artist1", "mbid": "", "playcount": 100}],
            "3month": [{"name": "Artist3", "mbid": "", "playcount": 10}],
            "12month": [{"name": "Artist2", "mbid": "", "playcount": 20}],
        }
        result = compute_match(payload_a, payload_b)
        self.assertIn("final_score", result)
        self.assertGreaterEqual(result["final_score"], 0)
        self.assertEqual(result["scores"]["overall"], 1.0)
        self.assertEqual(result["scores"]["12month"], 1.0)
        self.assertEqual(result["scores"]["3month"], 0.0)
