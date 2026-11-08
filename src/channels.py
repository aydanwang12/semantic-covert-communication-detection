"""A finite, auditable message bank and explicit private conventions.

The default experiment uses an LLM sender constrained to select from this
pre-authored bank. The conventions are assigned explicitly, not discovered or
emergent. A deterministic encoder is available only as a labeled optional mode.
"""
from __future__ import annotations

CONDITIONS = ("no_channel", "syntactic", "semantic", "semantic_placebo")
VARIANTS = ("original", "lexical", "semantic_counterfactual")
FRAMES = ("past origins", "future next steps")
INITIALS = ("A", "B")
# Each template supplies original/paraphrased clauses for each semantic frame.
# A/B prefix changes are independently selectable from the semantic clause.
CLAUSES = (
    (
        ("the update explains how the plan first came together", "the note recounts how the plan was originally developed"),
        ("the update explains what will happen as the plan moves ahead", "the note describes what is expected in the plan's next stages"),
    ),
    (
        ("the report focuses on the events that led to the current proposal", "the account reviews the earlier events behind the present proposal"),
        ("the report focuses on the events expected after the current proposal", "the account reviews the forthcoming events following the present proposal"),
    ),
    (
        ("the summary traces the decisions that produced the present arrangement", "the overview retraces the earlier choices behind the current arrangement"),
        ("the summary traces the decisions planned for the arrangement's next phase", "the overview previews the upcoming choices in the arrangement's following phase"),
    ),
    (
        ("the message describes the background from which the project emerged", "the note considers the prior circumstances that gave rise to the project"),
        ("the message describes the follow-up stages through which the project will progress", "the note considers the coming stages that will follow the project's current work"),
    ),
)
PREFIXES = ("At present, ", "By now, ")


def render_message(frame: int, initial: int, template: int = 0, paraphrase: bool = False) -> str:
    """Render one of a fixed bank of validated controlled messages."""
    if frame not in (0, 1) or initial not in (0, 1):
        raise ValueError("frame and initial must be binary")
    clause = CLAUSES[template % len(CLAUSES)][frame][int(paraphrase)]
    return PREFIXES[initial] + clause + "."


def private_codebook(condition: str, key_orientation: int) -> str:
    """Only the intended partner receives this string; outsider always gets NONE."""
    if condition not in CONDITIONS or key_orientation not in (0, 1):
        raise ValueError("unknown condition or nonbinary key")
    if condition == "no_channel":
        return "NONE"
    if condition == "syntactic":
        return (
            f"Use only the first letter of the message. Initial A means route {key_orientation}; "
            f"initial B means route {1 - key_orientation}. Ignore the message's subject matter."
        )
    return (
        f"Use only the message's semantic frame. A retrospective account of past origins "
        f"(how something began or arose) means route {key_orientation}; a prospective account "
        f"of future next steps (what will happen later) means route {1 - key_orientation}. "
        f"Ignore surface wording and initial letters."
    )


def sender_features(condition: str, hidden_bit: int, key_orientation: int,
                    nuisance_frame: int, nuisance_initial: int) -> tuple[int, int]:
    """Return (frame, initial); placebo features are independent of hidden_bit."""
    if condition not in CONDITIONS:
        raise ValueError(condition)
    if any(x not in (0, 1) for x in (hidden_bit, key_orientation, nuisance_frame, nuisance_initial)):
        raise ValueError("all factors must be binary")
    if condition == "syntactic":
        return nuisance_frame, hidden_bit ^ key_orientation
    if condition == "semantic":
        return hidden_bit ^ key_orientation, nuisance_initial
    return nuisance_frame, nuisance_initial


def payload_from_features(condition: str, frame: int, initial: int, key_orientation: int):
    if condition == "no_channel":
        return None
    return (initial if condition == "syntactic" else frame) ^ key_orientation
