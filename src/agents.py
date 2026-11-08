"""Isolated LLM calls through the authenticated Codex CLI or OpenAI API.

Never cache or synthesize experimental responses. Each call gets a fresh context.
No credentials are written into experimental records.
The optional API backend reads its key only from the environment.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request
from dataclasses import asdict, dataclass


@dataclass
class ModelResult:
    response_text: str | None
    backend: str
    model: str
    elapsed_seconds: float
    raw_stdout: str = ""
    raw_stderr: str = ""
    error: str | None = None
    tool_use_detected: bool = False
    usage: dict | None = None
    returncode: int | None = None

    def to_dict(self):
        return asdict(self)


def parse_action(text: str | None):
    """Strict JSON action parsing: bools, floats, extra keys and prose are invalid."""
    if not text:
        return None
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or set(obj) != {"action"}:
        return None
    value = obj["action"]
    return value if type(value) is int and value in (0, 1) else None


def parse_sender_message(text: str | None, candidates: list[str]):
    if not text:
        return None
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or set(obj) != {"message"}:
        return None
    value = obj["message"]
    return value if isinstance(value, str) and value in candidates else None


class CodexBackend:
    """Fresh ephemeral CLI session in an empty temporary directory per call."""
    name = "codex_cli"

    def __init__(self, model="gpt-6.1-sol", reasoning_effort="low", timeout=90,
                 executable="codex", model_instructions_file=None):
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout = timeout
        self.executable = executable
        self.model_instructions_file = model_instructions_file

    def complete(self, system: str, prompt: str) -> ModelResult:
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="covert-llm-") as taskdir:
            output = Path(taskdir) / "response.txt"
            instruction_path = None
            if self.model_instructions_file:
                instruction_path = Path(taskdir) / "instructions.txt"
                instruction_path.write_text(Path(self.model_instructions_file).read_text())
            args = [self.executable, "--no-daemon", "exec", "--ephemeral",
                    "--ignore-user-config", "--skip-git-repo-check", "--cd", taskdir,
                    "--sandbox", "read-only", "--json", "-m", self.model,
                    "-c", f'model_reasoning_effort="{self.reasoning_effort}"',
                    "-c", "project_doc_max_bytes=0", "-c", 'web_search="disabled"',
                    "-o", str(output)]
            if instruction_path:
                args.extend(["-c", f"model_instructions_file={json.dumps(str(instruction_path))}"])
            args.append("-")
            combined_prompt = (
                "This is a single isolated research trial. Do not call tools, read files, "
                "browse the web, or inspect your environment. Answer only the supplied task.\n\n"
                + system + "\n\n" + prompt
            )
            stdout = stderr = ""
            error = None
            returncode = None
            try:
                proc = subprocess.run(args, input=combined_prompt, text=True, capture_output=True,
                                      timeout=self.timeout, check=False, cwd=taskdir)
                stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
                if returncode:
                    error = f"process_exit_{returncode}"
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or ""
                stderr = exc.stderr or ""
                if isinstance(stdout, bytes):
                    stdout = stdout.decode("utf-8", errors="replace")
                if isinstance(stderr, bytes):
                    stderr = stderr.decode("utf-8", errors="replace")
                error = "timeout"
            except OSError as exc:
                error = f"{type(exc).__name__}: {exc}"
            stderr = stderr.replace(str(Path.home()), "<HOME>")
            response = output.read_text() if output.exists() else None
            usage = None
            tool_use = False
            for line in stdout.splitlines():
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                item = event.get("item", {})
                if event.get("type") == "turn.completed":
                    usage = event.get("usage")
                if item.get("type") in {"command_execution", "mcp_tool_call", "web_search", "file_change", "tool_call"}:
                    tool_use = True
                if "tool" in item.get("type", ""):
                    tool_use = True
            if tool_use:
                error = "unexpected_tool_use"
            return ModelResult(response, self.name, self.model, time.monotonic() - started,
                               stdout, stderr, error, tool_use, usage, returncode)


class OpenAIBackend:
    """Optional direct API backend; not used for the bundled Codex CLI dataset."""
    name = "openai_chat_completions"

    def __init__(self, model, timeout=90):
        self.model, self.timeout = model, timeout

    def complete(self, system: str, prompt: str) -> ModelResult:
        started = time.monotonic()
        payload = {"model": self.model, "messages": [
            {"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}}
        response = raw = ""
        error = None
        usage = None
        try:
            key = os.environ["OPENAI_API_KEY"]
            request = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode(), method="POST",
                headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
            with urllib.request.urlopen(request, timeout=self.timeout) as stream:
                raw = stream.read().decode()
            obj = json.loads(raw)
            response = obj["choices"][0]["message"]["content"]
            usage = obj.get("usage")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        return ModelResult(response or None, self.name, self.model, time.monotonic()-started,
                           raw_stdout=raw, error=error, usage=usage)
