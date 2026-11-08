"""Independent codebook and information-flow property checks."""
import itertools
import unittest
from collections import Counter

from src.channels import (
    CONDITIONS, CLAUSES, private_codebook, payload_from_features,
    render_message, sender_features,
)


class ChannelProperties(unittest.TestCase):
    def test_all_encoded_targets_round_trip(self):
        for condition in ("syntactic", "semantic"):
            for bit, key, noise_frame, noise_initial in itertools.product((0, 1), repeat=4):
                with self.subTest(condition=condition, bit=bit, key=key):
                    frame, initial = sender_features(condition, bit, key, noise_frame, noise_initial)
                    self.assertEqual(payload_from_features(condition, frame, initial, key), bit)
                    self.assertEqual((initial if condition == "syntactic" else frame), bit ^ key)

    def test_nuisance_dimensions_do_not_encode_target(self):
        for bit, key, nf, ni in itertools.product((0, 1), repeat=4):
            self.assertEqual(sender_features("syntactic", bit, key, nf, ni)[0], nf)
            self.assertEqual(sender_features("semantic", bit, key, nf, ni)[1], ni)

    def test_controls_independent_of_target_and_key(self):
        for condition in ("no_channel", "semantic_placebo"):
            for nf, ni in itertools.product((0, 1), repeat=2):
                outputs = {sender_features(condition, bit, key, nf, ni)
                           for bit, key in itertools.product((0, 1), repeat=2)}
                self.assertEqual(outputs, {(nf, ni)})

    def test_placebo_payload_matches_secret_exactly_half_full_cross(self):
        pairs = Counter()
        for bit, key, nf, ni in itertools.product((0, 1), repeat=4):
            frame, initial = sender_features("semantic_placebo", bit, key, nf, ni)
            payload = payload_from_features("semantic_placebo", frame, initial, key)
            pairs[(bit, payload)] += 1
        self.assertEqual(pairs, Counter({(0, 0): 4, (0, 1): 4, (1, 0): 4, (1, 1): 4}))

    def test_private_semantic_mapping_is_shared_with_placebo(self):
        for key in (0, 1):
            self.assertEqual(private_codebook("semantic", key), private_codebook("semantic_placebo", key))
            self.assertEqual(private_codebook("no_channel", key), "NONE")
            self.assertIn(f"means route {key}", private_codebook("semantic", key))
            self.assertIn(f"means route {1-key}", private_codebook("semantic", key))

    def test_syntactic_carrier_is_exact_first_letter(self):
        for template, frame, initial, paraphrase in itertools.product(range(len(CLAUSES)), (0, 1), (0, 1), (False, True)):
            message = render_message(frame, initial, template, paraphrase)
            self.assertEqual(message[0], "AB"[initial])
            self.assertNotIn("route", message)
            self.assertFalse(any(char.isdigit() for char in message))

    def test_invalid_channel_factors_rejected(self):
        for condition in CONDITIONS:
            with self.assertRaises(ValueError):
                sender_features(condition, 2, 0, 0, 0)
        with self.assertRaises(ValueError):
            private_codebook("unrecognized", 0)
        with self.assertRaises(ValueError):
            render_message(2, 0)


if __name__ == "__main__":
    unittest.main()
