"""Strict parsing, isolated backend calls, and raw-data failure preservation."""
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.agents import CodexBackend, ModelResult, parse_action, parse_sender_message
from src.environment import generate_episodes, sender_task
from experiments.run_experiment import run_episode, append_jsonl


class SequenceBackend:
    """Unit-test fixture only; its outputs must never be scientific observations."""
    name = "unit_test_fixture"
    model = "none"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def complete(self, system, prompt):
        self.calls.append((system, prompt))
        value = next(self.responses)
        return value if isinstance(value, ModelResult) else ModelResult(value, self.name, self.model, 0)


class AgentParsingTests(unittest.TestCase):
    def test_only_exact_binary_integer_json_is_valid(self):
        for bit in (0, 1):
            self.assertEqual(parse_action(json.dumps({"action": bit})), bit)
        for value in (None, "", "0", "[]", "null", '{"action":true}', '{"action":0.0}',
                      '{"action":"1"}', '{"action":2}', '{"action":0,"why":"x"}',
                      '```json\n{"action":0}\n```', 'Answer: {"action":0}'):
            with self.subTest(value=value):
                self.assertIsNone(parse_action(value))

    def test_sender_output_must_be_exact_approved_message(self):
        candidates = ["At present, one.", "By now, two."]
        self.assertEqual(parse_sender_message(json.dumps({"message": candidates[1]}), candidates), candidates[1])
        for value in ('{"message":"Unapproved."}', '{"message":0}',
                      '{"message":"At present, one.","extra":true}', "At present, one."):
            self.assertIsNone(parse_sender_message(value, candidates))


class BackendIsolationTests(unittest.TestCase):
    def test_fresh_empty_cwd_and_complete_raw_events(self):
        working_dirs = []
        raw = json.dumps({"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":4}}) + "\n"
        def fake_run(args, **kwargs):
            directory = Path(kwargs["cwd"])
            working_dirs.append(directory)
            self.assertEqual(list(directory.iterdir()), [])
            self.assertIn("--ephemeral", args)
            self.assertIn("--ignore-user-config", args)
            self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
            self.assertEqual(args[args.index("--cd") + 1], str(directory))
            self.assertIn("Do not call tools", kwargs["input"])
            self.assertNotIn("shell", kwargs)
            Path(args[args.index("-o") + 1]).write_text('{"action":1}')
            return SimpleNamespace(stdout=raw, stderr=str(Path.home()) + "/safe-warning", returncode=0)
        with patch("src.agents.subprocess.run", side_effect=fake_run):
            backend = CodexBackend()
            first = backend.complete("SYSTEM", "PROMPT")
            second = backend.complete("SYSTEM", "PROMPT")
        self.assertEqual(len(set(working_dirs)), 2)
        self.assertTrue(all(not p.exists() for p in working_dirs))
        self.assertEqual(first.raw_stdout, raw)
        self.assertEqual(first.response_text, '{"action":1}')
        self.assertEqual(first.usage["output_tokens"], 4)
        self.assertIsNone(first.error)
        self.assertNotIn(str(Path.home()), first.raw_stderr)
        self.assertEqual(second.returncode, 0)

    def test_tool_event_invalidates_even_valid_answer(self):
        for kind in ("command_execution", "mcp_tool_call", "web_search", "file_change", "tool_call"):
            def fake_run(args, **kwargs):
                Path(args[args.index("-o") + 1]).write_text('{"action":0}')
                return SimpleNamespace(stdout=json.dumps({"type":"item.completed", "item":{"type":kind}}), stderr="", returncode=0)
            with self.subTest(kind=kind), patch("src.agents.subprocess.run", side_effect=fake_run):
                result = CodexBackend().complete("S", "P")
                self.assertEqual(result.error, "unexpected_tool_use")
                self.assertTrue(result.tool_use_detected)
                self.assertEqual(result.response_text, '{"action":0}')

    def test_timeout_retains_partial_raw_output(self):
        error = subprocess.TimeoutExpired("codex", 1, output=b'partial stdout', stderr=b'partial stderr')
        with patch("src.agents.subprocess.run", side_effect=error):
            result = CodexBackend().complete("S", "P")
        self.assertEqual(result.error, "timeout")
        self.assertEqual(result.raw_stdout, "partial stdout")
        self.assertEqual(result.raw_stderr, "partial stderr")
        self.assertIsNone(result.response_text)


class ExperimentPersistenceTests(unittest.TestCase):
    def episode(self, condition):
        return next(e for e in generate_episodes() if e["condition"] == condition)

    def test_invalid_sender_saved_and_receiver_not_called(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "calls.jsonl"
            backend = SequenceBackend(["not JSON"])
            row = run_episode(self.episode("semantic"), backend, ledger, threading.Lock())
            self.assertEqual(len(backend.calls), 1)
            self.assertEqual(row["episode_status"], "invalid_sender_no_receiver_calls")
            self.assertFalse(row["sender_valid"])
            self.assertTrue(all(a is None for values in row["actions"].values() for a in values.values()))
            records = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["response_text"], "not JSON")
            self.assertFalse(records[0]["valid"])

    def test_valid_but_wrong_sender_choice_is_not_repaired(self):
        episode = self.episode("semantic")
        _, candidates, features = sender_task(episode)
        wrong_index = 1 - (episode["hidden_bit"] ^ episode["key_orientation"])
        wrong = candidates[wrong_index]
        backend = SequenceBackend([json.dumps({"message":wrong})] + ['{"action":0}'] * 8)
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "calls.jsonl"
            row = run_episode(episode, backend, ledger, threading.Lock())
            self.assertEqual(row["messages"]["original"], wrong)
            self.assertNotEqual(row["encoded_bit"], row["hidden_bit"])
            self.assertEqual(len(backend.calls), 9)
            self.assertEqual(len(ledger.read_text().splitlines()), 9)
            self.assertEqual(row["messages"]["unchanged_repeat"], row["messages"]["original"])
            for role in ("partner", "outsider"):
                self.assertEqual(row["prompts"][role]["unchanged_repeat"], row["prompts"][role]["original"])

    def test_invalid_receiver_stays_missing_and_raw_response_saved(self):
        episode = self.episode("syntactic")
        _, candidates, _ = sender_task(episode)
        backend = SequenceBackend([json.dumps({"message":candidates[0]}), "malformed"] + ['{"action":1}'] * 7)
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "calls.jsonl"
            row = run_episode(episode, backend, ledger, threading.Lock())
            self.assertEqual(row["episode_status"], "complete_with_invalid_responses")
            values = [a for actions in row["actions"].values() for a in actions.values()]
            self.assertEqual(values.count(None), 1)
            records = [json.loads(line) for line in ledger.read_text().splitlines()]
            invalid = [r for r in records if not r["valid"]]
            self.assertEqual(len(invalid), 1)
            self.assertEqual(invalid[0]["response_text"], "malformed")
            self.assertIsNone(invalid[0]["action"])
            self.assertEqual(len(records), 9)

    def test_backend_error_invalidates_parseable_response(self):
        episode = self.episode("syntactic")
        _, candidates, _ = sender_task(episode)
        bad = ModelResult('{"action":1}', "unit_test_fixture", "none", 0, error="timeout")
        backend = SequenceBackend([json.dumps({"message":candidates[0]}), bad] + ['{"action":0}'] * 7)
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "calls.jsonl"
            row = run_episode(episode, backend, ledger, threading.Lock())
            self.assertEqual(sum(a is None for actions in row["actions"].values() for a in actions.values()), 1)
            record = next(json.loads(line) for line in ledger.read_text().splitlines() if json.loads(line).get("error"))
            self.assertEqual(record["response_text"], '{"action":1}')
            self.assertFalse(record["valid"])

    def test_jsonl_round_trip_retains_unicode_and_append_order(self):
        lock = threading.Lock()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.jsonl"
            values = [{"message":"naïve →", "action":None}, {"message":"next", "action":1}]
            for value in values:
                append_jsonl(path, value, lock)
            self.assertEqual([json.loads(line) for line in path.read_text().splitlines()], values)


class FrameValidationTests(unittest.TestCase):
    def test_bank_coverage_and_blinding(self):
        from experiments.validate_frames import bank, frame_prompt
        records = bank()
        self.assertEqual(len(records), 32)
        self.assertEqual(len({row["validation_id"] for row in records}), 32)
        self.assertEqual(len({row["message"] for row in records}), 32)
        for row in records:
            prompt = frame_prompt(row["message"])
            self.assertNotIn("route", prompt)
            self.assertNotIn("codebook", prompt)
            self.assertNotIn("Hidden target", prompt)
            self.assertNotIn("expected_frame", prompt)

    def test_frame_parser_and_missing_label_denominators(self):
        from experiments.validate_frames import bank, parse_frame, summarize
        self.assertEqual(parse_frame('{"frame":0}'), 0)
        self.assertEqual(parse_frame('{"frame":1}'), 1)
        for text in (None, '{"frame":true}', '{"frame":1.0}', '{"frame":2}', '{"frame":0,"why":"x"}'):
            self.assertIsNone(parse_frame(text))
        rows = [{**r, "predicted_frame":r["expected_frame"], "valid":True, "correct":True} for r in bank()]
        full = summarize(rows)
        self.assertEqual(full["correct_labels"], 32)
        self.assertEqual(full["all_labels_correct_sets"], 16)
        self.assertEqual(full["lexical_preservation_successes"], 16)
        self.assertEqual(full["semantic_change_successes"], 16)
        rows[0].update(predicted_frame=None, valid=False, correct=False)
        incomplete = summarize(rows)
        self.assertEqual(incomplete["label_accuracy_all_attempts"], 31/32)
        self.assertEqual(incomplete["invalid_responses"], 1)
        self.assertLess(incomplete["all_labels_correct_sets"], 16)


if __name__ == "__main__":
    unittest.main()
