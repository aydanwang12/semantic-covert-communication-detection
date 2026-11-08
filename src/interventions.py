"""Orthogonal, pre-authored lexical and semantic interventions.

Validation is exact against the reviewed finite bank. This is not an independent
LLM or human semantic rating, nor evidence about unconstrained paraphrasing.
"""
from __future__ import annotations
from .channels import render_message


def make_interventions(frame: int, initial: int, template: int = 0) -> dict[str, str]:
    return {
        "original": render_message(frame, initial, template, False),
        "lexical": render_message(frame, 1 - initial, template, True),
        "semantic_counterfactual": render_message(1 - frame, initial, template, False),
    }


def validate_interventions(messages: dict[str, str], frame: int, initial: int,
                           template: int = 0) -> dict:
    expected = make_interventions(frame, initial, template)
    original_ok = messages.get("original") == expected["original"]
    lexical_ok = original_ok and messages.get("lexical") == expected["lexical"]
    counterfactual_ok = original_ok and messages.get("semantic_counterfactual") == expected["semantic_counterfactual"]
    return {
        "original": original_ok,
        "lexical": lexical_ok,
        "semantic_counterfactual": counterfactual_ok,
        "method": "exact match to pre-authored, manually reviewed finite template bank",
        "lexical_preserves_frame": lexical_ok,
        "lexical_flips_initial": lexical_ok,
        "semantic_changes_frame": counterfactual_ok,
        "semantic_preserves_initial": counterfactual_ok,
    }
