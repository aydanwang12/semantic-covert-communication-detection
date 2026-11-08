"""Regression for a removed, unused design option that leaked the placebo target."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.environment import generate_episodes

ROOT = Path(__file__).resolve().parents[1]


class FractionSafetyTests(unittest.TestCase):
    def placebo(self):
        return [r for r in generate_episodes(replicates=1) if r["condition"] == "semantic_placebo"]

    def test_former_parity_fraction_reveals_target_from_joint_observables(self):
        rows = self.placebo()
        fraction = [r for r in rows if r["nuisance_initial"] ==
                    (r["hidden_bit"] ^ r["key_orientation"] ^ r["nuisance_frame"])]
        self.assertEqual(len(fraction), 8)
        # Balanced marginals do not imply absence of a higher-order channel.
        for factor in ("hidden_bit", "key_orientation", "frame", "initial"):
            self.assertEqual(Counter(r[factor] for r in fraction), {0: 4, 1: 4})
        self.assertTrue(all(r["hidden_bit"] == (r["initial"] ^ r["key_orientation"] ^ r["frame"])
                            for r in fraction))
        by_observation = defaultdict(set)
        for row in fraction:
            by_observation[(row["key_orientation"], row["frame"], row["initial"])].add(row["hidden_bit"])
        self.assertEqual(len(by_observation), 8)
        self.assertTrue(all(len(targets) == 1 for targets in by_observation.values()))

    def test_full_cross_has_no_joint_placebo_target_leak(self):
        rows = self.placebo()
        self.assertEqual(len(rows), 16)
        distributions = {target: Counter((r["key_orientation"], r["frame"], r["initial"])
                                        for r in rows if r["hidden_bit"] == target)
                         for target in (0, 1)}
        self.assertEqual(distributions[0], distributions[1])
        by_observation = defaultdict(Counter)
        for row in rows:
            by_observation[(row["key_orientation"], row["frame"], row["initial"])][row["hidden_bit"]] += 1
        self.assertTrue(all(targets == {0: 1, 1: 1} for targets in by_observation.values()))
        parity_correct = sum(r["hidden_bit"] == (r["initial"] ^ r["key_orientation"] ^ r["frame"])
                             for r in rows)
        self.assertEqual(parity_correct, 8)

    def test_cli_rejects_unsafe_fraction_before_creating_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "unused.jsonl"
            completed = subprocess.run([sys.executable, str(ROOT / "experiments/run_experiment.py"),
                                        "--limit-blocks", "8", "--plan-only", "--output", str(output)],
                                       text=True, capture_output=True)
            self.assertEqual(completed.returncode, 2)
            self.assertRegex(completed.stderr, r"invalid choice: ['\"]?8['\"]?")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_cli_explicit_full_cross_is_supported_without_model_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            config = json.loads((ROOT / "config/experiment.json").read_text())
            # Plan-only does not instantiate a backend; this avoids CLI version probing.
            config.update(backend="openai_chat_completions", model_instructions_file=None)
            config_path = folder / "config.json"
            config_path.write_text(json.dumps(config))
            output = folder / "plan.jsonl"
            completed = subprocess.run([sys.executable, str(ROOT / "experiments/run_experiment.py"),
                                        "--config", str(config_path), "--split", "pilot",
                                        "--limit-blocks", "16", "--plan-only", "--output", str(output)],
                                       text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["planned_episodes"], 64)
            self.assertEqual(result["model_calls"], 0)
            manifest = json.loads(output.with_suffix(".manifest.json").read_text())
            self.assertEqual(manifest["limit_blocks"], 16)
            self.assertEqual(manifest["planned_episode_count"], 64)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".calls.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
