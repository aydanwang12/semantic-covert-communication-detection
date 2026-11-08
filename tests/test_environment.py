"""Design, balance, matched prompts and leakage checks."""
import itertools
import unittest
from collections import Counter, defaultdict

from src.channels import CONDITIONS
from src.environment import generate_episodes, PUBLIC_CONTEXT


class EnvironmentProperties(unittest.TestCase):
    def test_complete_cross_and_matched_blocks(self):
        episodes = generate_episodes("main", replicates=2)
        self.assertEqual(len(episodes), 128)
        self.assertEqual(len({row["episode_id"] for row in episodes}), 128)
        blocks = defaultdict(list)
        for row in episodes:
            blocks[row["block_id"]].append(row)
        self.assertEqual(len(blocks), 32)
        for rows in blocks.values():
            self.assertEqual({row["condition"] for row in rows}, set(CONDITIONS))
            self.assertEqual(len({(r["hidden_bit"], r["key_orientation"], r["nuisance_frame"], r["nuisance_initial"]) for r in rows}), 1)
        for condition in CONDITIONS:
            rows = [row for row in episodes if row["condition"] == condition]
            counts = Counter((r["hidden_bit"], r["key_orientation"], r["nuisance_frame"], r["nuisance_initial"]) for r in rows)
            self.assertEqual(counts, Counter({factors: 2 for factors in itertools.product((0, 1), repeat=4)}))

    def test_prompts_differ_only_in_private_convention(self):
        for row in generate_episodes():
            for variant, outsider in row["prompts"]["outsider"].items():
                partner = row["prompts"]["partner"][variant]
                expected = partner.replace("Private convention: " + row["private_codebook"], "Private convention: NONE", 1)
                self.assertEqual(outsider, expected)
                self.assertIn(PUBLIC_CONTEXT, outsider)
                self.assertIn(row["messages"][variant], outsider)
                self.assertNotIn(row["episode_id"], outsider)
                self.assertNotIn("Initial A means", outsider)
                self.assertNotIn("past origins (how something began or arose) means", outsider)
            if row["condition"] == "no_channel":
                self.assertEqual(row["prompts"]["partner"], row["prompts"]["outsider"])

    def test_outsider_observable_distribution_does_not_reveal_target(self):
        for condition in CONDITIONS:
            rows = [r for r in generate_episodes(replicates=2) if r["condition"] == condition]
            for variant in ("original", "lexical", "semantic_counterfactual"):
                target0 = Counter(r["prompts"]["outsider"][variant] for r in rows if r["hidden_bit"] == 0)
                target1 = Counter(r["prompts"]["outsider"][variant] for r in rows if r["hidden_bit"] == 1)
                self.assertEqual(target0, target1)

    def test_control_partner_observations_independent_of_target(self):
        for condition in ("no_channel", "semantic_placebo"):
            rows = [r for r in generate_episodes(replicates=2) if r["condition"] == condition]
            for variant in ("original", "lexical", "semantic_counterfactual"):
                left = Counter(r["prompts"]["partner"][variant] for r in rows if r["hidden_bit"] == 0)
                right = Counter(r["prompts"]["partner"][variant] for r in rows if r["hidden_bit"] == 1)
                self.assertEqual(left, right)

    def test_seed_changes_order_not_design_and_splits_disjoint(self):
        first = generate_episodes(seed=1)
        second = generate_episodes(seed=2)
        self.assertNotEqual([r["episode_id"] for r in first], [r["episode_id"] for r in second])
        self.assertEqual({r["episode_id"] for r in first}, {r["episode_id"] for r in second})
        self.assertEqual(first, generate_episodes(seed=1))
        self.assertFalse({r["episode_id"] for r in generate_episodes("pilot")} & {r["episode_id"] for r in first})

    def test_invalid_design_size_rejected(self):
        with self.assertRaises(ValueError):
            generate_episodes(replicates=0)
        with self.assertRaises(ValueError):
            generate_episodes(split="unknown")


if __name__ == "__main__":
    unittest.main()
