import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("target_audit", Path(__file__).resolve().parents[1] / "analysis/target_conditioned_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class TargetConditionedAuditTests(unittest.TestCase):
    def test_exact_sign_distribution_known_extremes(self):
        self.assertEqual(audit.sign_flip_reference([1, 1, 1])["one_sided_alignment_p"], 1 / 8)
        self.assertEqual(audit.sign_flip_reference([1, 1, 1])["two_sided_p"], 1 / 4)
        self.assertEqual(audit.sign_flip_reference([0, 0])["two_sided_p"], 1)
        self.assertEqual(audit.sign_flip_reference([1, -1])["two_sided_p"], 1)

    def test_rejects_empty_and_boolean_inputs(self):
        for inputs in ([], [True], [2], [0.5]):
            with self.assertRaises(ValueError):
                audit.sign_flip_reference(inputs)

    def test_missing_pair_is_reported_not_imputed(self):
        row = dict(episode_id="a", split="main", condition="semantic", replicate=0,
                   template_index=0, key_orientation=0, nuisance_frame=0,
                   nuisance_initial=0, hidden_bit=0, actions={"partner": {"original": 0}})
        result = audit.audit_rows([row])["main"]["semantic"]["partner"]
        self.assertEqual(result["eligible_pairs"], 0)
        self.assertIsNone(result["paired_target_response"])
        self.assertEqual(result["excluded_pairs"][0]["reason"], "missing_target_counterpart")


if __name__ == "__main__":
    unittest.main()
