import unittest

from src.detection import condition_contrast, corrected_gap, detector_score, gap, repeat_gap, response_quality, summarize, validate_dataset
from src.metrics import cluster_bootstrap, flip_gap, is_binary, percentile, roc_auc, wilson_interval


def row(episode_id="one", condition="semantic", partner=(0, 0, 1), outsider=(0, 0, 0), hidden_bit=0, block_id="block"):
    variants = ("original", "lexical", "semantic_counterfactual")
    return {"episode_id": episode_id, "block_id": block_id, "split": "test", "condition": condition,
            "hidden_bit": hidden_bit, "key_orientation": 0,
            "actions": {"partner": dict(zip(variants, partner)), "outsider": dict(zip(variants, outsider))},
            "intervention_validation": {"lexical": True, "semantic_counterfactual": True}}


class MetricsTests(unittest.TestCase):
    def test_known_gap_directions(self):
        self.assertEqual(flip_gap(0, 1, 0, 0), 1)
        self.assertEqual(flip_gap(1, 1, 0, 1), -1)
        self.assertEqual(flip_gap(1, 0, 0, 1), 0)
        self.assertEqual(flip_gap(1, 1, 0, 0), 0)

    def test_gap_symmetry_in_actions(self):
        for p0 in (0, 1):
            for p1 in (0, 1):
                for o0 in (0, 1):
                    for o1 in (0, 1):
                        self.assertEqual(flip_gap(p0, p1, o0, o1), -flip_gap(o0, o1, p0, p1))

    def test_invalid_actions_not_coerced(self):
        for value in (None, True, False, "0", "1", 2, -1, 0.0):
            self.assertFalse(is_binary(value))
            self.assertIsNone(flip_gap(value, 1, 0, 0))

    def test_auc_ties_and_direction(self):
        self.assertEqual(roc_auc([1, 1], [0, 0]), 1)
        self.assertEqual(roc_auc([0, 0], [1, 1]), 0)
        self.assertEqual(roc_auc([1, 1], [1, 1]), .5)
        self.assertEqual(roc_auc([0, 1], [0, 1]), .5)
        self.assertIsNone(roc_auc([], [0]))
        self.assertIsNone(roc_auc([0], []))

    def test_wilson_boundaries(self):
        self.assertIsNone(wilson_interval(0, 0))
        lower, upper = wilson_interval(0, 10)
        self.assertAlmostEqual(lower, 0)
        self.assertTrue(0 < upper < 1)
        lower, upper = wilson_interval(10, 10)
        self.assertTrue(0 < lower < 1)
        self.assertAlmostEqual(upper, 1)
        with self.assertRaises(ValueError):
            wilson_interval(11, 10)

    def test_percentile_interpolation(self):
        self.assertEqual(percentile([0, 10], .25), 2.5)
        self.assertEqual(percentile([7], .025), 7)

    def test_cluster_resampling_keeps_pairs(self):
        records = [{"block_id": str(i), "episode_id": f"{i}-{j}", "value": (-1) ** j * (i + 1)}
                   for i in range(5) for j in range(2)]
        result = cluster_bootstrap(records, lambda sample: sum(r["value"] for r in sample), resamples=200)
        self.assertEqual(result["estimate"], 0)
        self.assertEqual(result["ci95_bootstrap"], [0, 0])
        self.assertEqual(result["n_clusters"], 5)

    def test_detector_threshold_and_validation(self):
        good = row()
        self.assertEqual(gap(good, "semantic_counterfactual"), 1)
        self.assertEqual(detector_score(good), 1)
        good["intervention_validation"]["lexical"] = False
        self.assertIsNone(detector_score(good))
        self.assertIsNone(gap(good, "lexical"))
        self.assertEqual(gap(good, "semantic_counterfactual"), 1)

    def test_primary_contrast_is_semantic_minus_syntactic(self):
        records = [row("sem", "semantic"), row("syn", "syntactic", partner=(0, 1, 0))]
        value = condition_contrast(records, "semantic_counterfactual", resamples=100)
        self.assertEqual(value["estimate"], 1)
        self.assertEqual(value["ci95_bootstrap"], [1, 1])
        self.assertEqual(value["n_clusters"], 1)

    def test_invalid_denominator_and_exclusions(self):
        records = [row("valid"), row("invalid", partner=(None, 0, 1), block_id="other")]
        result = summarize(records, resamples=50)["splits"]["test"]["conditions"]["semantic"]
        self.assertEqual(result["original_accuracy"]["partner"]["estimate"], .5)
        self.assertEqual(result["missing_or_invalid_receiver_action_rate"]["successes"], 1)
        self.assertEqual(result["missing_or_invalid_receiver_action_rate"]["n"], 12)
        self.assertEqual(result["interventions"]["lexical"]["n_excluded"], 1)
        self.assertEqual(result["detector"]["n_excluded"], 1)

    def test_placebo_can_alarm_without_payload_information(self):
        records = [row(f"p{i}", "semantic_placebo", hidden_bit=i % 2, block_id=str(i)) for i in range(4)]
        summary = summarize(records, resamples=50)["splits"]["test"]["conditions"]["semantic_placebo"]
        self.assertEqual(summary["original_accuracy"]["partner"]["estimate"], .5)
        self.assertEqual(summary["detector"]["alarm_rate"]["estimate"], 1)

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            validate_dataset([row(), row()])

    def test_repeat_noise_diagnostic_does_not_change_primary(self):
        record = row()
        record["actions"]["partner"]["unchanged_repeat"] = 1
        record["actions"]["outsider"]["unchanged_repeat"] = 0
        self.assertEqual(repeat_gap(record), 1)
        self.assertEqual(gap(record, "semantic_counterfactual"), 1)
        self.assertEqual(corrected_gap(record, "semantic_counterfactual"), 0)
        self.assertEqual(detector_score(record), 1)

    def test_skipped_receivers_not_invalid_attempts(self):
        record = row(partner=(None, None, None), outsider=(None, None, None))
        record["sender_response"] = {"valid": False}
        record["responses"] = {"partner": {}, "outsider": {}}
        quality = response_quality([record])
        self.assertEqual(quality["attempted_receiver_calls"], 0)
        self.assertEqual(quality["missing_or_invalid_receiver_outcomes"], 6)
        self.assertEqual(quality["sender_invalid_response_rate"]["estimate"], 1)
        self.assertIsNone(quality["receiver_invalid_response_rate"]["estimate"])

    def test_empty_summary_no_fabricated_rates(self):
        self.assertEqual(summarize([], resamples=20)["splits"], {})


if __name__ == "__main__":
    unittest.main()
