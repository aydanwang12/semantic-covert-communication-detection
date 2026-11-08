"""Independent semantic-cue and carrier checks across the finite message bank.

These checks operationalize the manual review of temporal clauses; they do not
establish semantic validity outside these authored messages.
"""
import itertools
import unittest
from src.channels import CLAUSES
from src.interventions import make_interventions, validate_interventions

# Cues were reviewed independently from the generator's frame labels.
PAST_CUES = ("first came together", "originally developed", "led to the current", "earlier events", "produced the present", "earlier choices", "project emerged", "gave rise")
FUTURE_CUES = ("will happen", "next stages", "expected after", "forthcoming events", "next phase", "upcoming choices", "will progress", "coming stages")


def independently_classify_frame(message):
    past = any(cue in message for cue in PAST_CUES)
    future = any(cue in message for cue in FUTURE_CUES)
    if past == future:
        raise AssertionError("Expected exactly one temporal-frame cue: " + message)
    return 0 if past else 1


class InterventionProperties(unittest.TestCase):
    def test_lexical_and_frame_perturbations_are_orthogonal(self):
        for template, frame, initial in itertools.product(range(len(CLAUSES)), (0, 1), (0, 1)):
            messages = make_interventions(frame, initial, template)
            with self.subTest(template=template, frame=frame, initial=initial):
                self.assertEqual(independently_classify_frame(messages["original"]), frame)
                self.assertEqual(independently_classify_frame(messages["lexical"]), frame)
                self.assertEqual(independently_classify_frame(messages["semantic_counterfactual"]), 1-frame)
                self.assertNotEqual(messages["original"][0], messages["lexical"][0])
                self.assertEqual(messages["original"][0], messages["semantic_counterfactual"][0])
                self.assertNotEqual(messages["original"], messages["lexical"])

    def test_all_bank_transformations_pass_validation(self):
        for template, frame, initial in itertools.product(range(len(CLAUSES)), (0, 1), (0, 1)):
            validation = validate_interventions(make_interventions(frame, initial, template), frame, initial, template)
            for key in ("original", "lexical", "semantic_counterfactual", "lexical_preserves_frame", "lexical_flips_initial", "semantic_changes_frame", "semantic_preserves_initial"):
                self.assertIs(validation[key], True)

    def test_changed_or_missing_variants_cannot_pass(self):
        for variant in ("original", "lexical", "semantic_counterfactual"):
            messages = make_interventions(0, 0)
            messages[variant] = "Unvalidated message."
            validation = validate_interventions(messages, 0, 0)
            self.assertIs(validation[variant], False)
            if variant == "original":
                self.assertIs(validation["lexical"], False)
                self.assertIs(validation["semantic_counterfactual"], False)
            messages.pop(variant)
            self.assertIs(validate_interventions(messages, 0, 0)[variant], False)


if __name__ == "__main__":
    unittest.main()
