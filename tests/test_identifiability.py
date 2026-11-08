"""Boundary tests for the posthoc certificate, independent of model responses."""
import itertools
from pathlib import Path
import tempfile
import unittest

from analysis.identifiability import analyze, distribution_certificate, finite_response_summary, receiver_view


def artificial_row():
    variants = ("original", "lexical", "semantic_counterfactual", "unchanged_repeat")
    prompts = {role: {v: f"{role}:{v}" for v in variants} for role in ("partner", "outsider")}
    return {"hidden_bit": 0, "condition": "semantic", "episode_id": "secret-id", "system_prompt": "same system",
            "public_context": "same public context", "private_codebook": "same codebook", "model": "same model", "backend": "same backend",
            "messages": {v: v for v in variants}, "prompts": prompts,
            "responses": {r: {v: {"prompt": p, "system_prompt": "same system", "recorded_at": "private time"}
                               for v, p in q.items()} for r, q in prompts.items()},
            "sender_response": {"prompt": "sender private"}}


class IdentifiabilityTests(unittest.TestCase):
    def test_equal_normalized_distributions_need_not_have_equal_multisets(self):
        result = distribution_certificate(["a", "b"], ["a", "a", "b", "b"])
        self.assertFalse(result["exact_multiset_equality"])
        self.assertEqual(result["empirical_query_distribution_total_variation"], 0)

    def test_counter_multiplicity_is_checked_not_only_support(self):
        result = distribution_certificate(["a", "a", "b"], ["a", "b", "b"])
        self.assertFalse(result["exact_multiset_equality"])
        self.assertAlmostEqual(result["empirical_query_distribution_total_variation"], 1/3)

    def test_exact_factorial_equivalence_and_target_exception(self):
        semantic, placebo, semantic_h, placebo_h = [], [], [], []
        for h, k, u, z in itertools.product((0, 1), repeat=4):
            semantic.append((k, h ^ k, z))
            placebo.append((k, u, z))
            semantic_h.append((k, h ^ k, z, h))
            placebo_h.append((k, u, z, h))
        self.assertTrue(distribution_certificate(semantic, placebo)["exact_multiset_equality"])
        self.assertEqual(distribution_certificate(semantic_h, placebo_h)["empirical_query_distribution_total_variation"], .5)

    def test_declared_metadata_exclusions_and_target_extension(self):
        left, right = artificial_row(), artificial_row()
        right.update(hidden_bit=1, condition="semantic_placebo", episode_id="different-id")
        right["responses"]["partner"]["original"]["recorded_at"] = "different time"
        right["sender_response"]["prompt"] = "different sender private"
        self.assertEqual(receiver_view(left), receiver_view(right))
        self.assertNotEqual(receiver_view(left, "target"), receiver_view(right, "target"))
        self.assertNotEqual(receiver_view(left, "sender_private_prompt"), receiver_view(right, "sender_private_prompt"))

    def test_real_record_prompt_mismatch_cannot_be_certified(self):
        row = artificial_row()
        row["responses"]["outsider"]["lexical"]["prompt"] += "hidden side information"
        with self.assertRaises(ValueError):
            receiver_view(row)

    def test_common_query_to_random_output_kernel_preserves_equality(self):
        # Exact finite probability calculation, not a simulated experiment.
        p, q = {"a": .5, "b": .5}, {"a": .5, "b": .5}
        kernel = {"a": {0: .1, 1: .9}, "b": {0: .8, 1: .2}}
        output = lambda distribution: {y: sum(distribution[x] * kernel[x][y] for x in distribution) for y in (0, 1)}
        self.assertEqual(output(p), output(q))
        score_distribution = output(p)
        auc = sum(pa * pb * ((a > b) + .5 * (a == b))
                  for a, pa in score_distribution.items() for b, pb in score_distribution.items())
        self.assertAlmostEqual(auc, .5)

    def test_privileged_paired_target_change_breaks_equivalence(self):
        for k, u in itertools.product((0, 1), repeat=2):
            semantic_frames = [h ^ k for h in (0, 1)]
            placebo_frames = [u for _ in (0, 1)]
            self.assertNotEqual(semantic_frames[0], semantic_frames[1])
            self.assertEqual(placebo_frames[0], placebo_frames[1])

    def test_empty_input_cannot_be_certified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.jsonl"
            path.write_text("")
            with self.assertRaises(ValueError):
                analyze([path])

    def test_invalid_actions_are_not_scored_as_flips(self):
        record = artificial_row()
        record["actions"] = {role: {v: None for v in ("original", "lexical", "semantic_counterfactual")}
                             for role in ("partner", "outsider")}
        result = finite_response_summary([record], [record])
        self.assertIsNone(result["realized_prespecified_detector_auc"])
        self.assertEqual(result["n_invalid_score_excluded_semantic"], 1)
        self.assertEqual(result["n_invalid_score_excluded_placebo"], 1)


if __name__ == "__main__":
    unittest.main()
