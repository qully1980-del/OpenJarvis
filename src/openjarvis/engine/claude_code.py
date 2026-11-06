"""Motor "Claude Code" — usa el Claude Code instalado en este equipo en modo headless.

Cada petición lanza ``claude -p`` (modo no interactivo) con la conversación por
stdin y lee la respuesta en streaming (``--output-format stream-json``). Así se
aprovecha la suscripción con la que el usuario ya inició sesión en Claude Code,
sin claves de API ni gasto adicional.

Decisiones de seguridad y privacidad:

* Sin herramientas (``--tools ""``) ni servidores MCP (``--strict-mcp-config``):
  Claude Code solo genera texto, no puede leer archivos ni ejecutar comandos.
* Sin ajustes, hooks ni CLAUDE.md del usuario (``--setting-sources ""``) y en
  una carpeta vacía propia, para que no arrastre contexto de ningún proyecto.
* Sin sesiones guardadas (``--no-session-persistence``).
* Se elimina ``ANTHROPIC_API_KEY`` del entorno del proceso hijo para que use
  siempre la sesión de la suscripción y nunca facture contra una clave de API.
* ``is_cloud`` es False a propósito: el servidor trata los motores "cloud" con
  un atajo que los desviaría a Ollama. Este motor gestiona su propio transporte.

Los modelos se exponen como ``claudecode/<alias>`` (opus, sonnet, haiku); el
alias lo resuelve Claude Code al modelo más reciente de esa familia.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import threading
from collections.abc import AsyncIterator, Iterator, Sequence
from pathlib import Path
from typing import Any, Dict, List, Optional

from openjarvis.core.registry import EngineRegistry
from openjarvis.core.types import Message, Role
from openjarvis.engine._base import InferenceEngine, estimate_prompt_tokens

logger = logging.getLogger(__name__)

MODEL_PREFIX = "claudecode/"
_ALIASES = ("sonnet", "opus", "haiku")
_TIMEOUT_S = 600
_SANDBOX = Path.home() / ".openjarvis" / "claude-code-sandbox"


def _find_cli() -> Optional[str]:
    override = os.environ.get("OPENJARVIS_CLAUDE_CLI")
    if override and Path(override).exists():
        return override
    found = shutil.which("claude")
    if found:
        return found
    for candidate in (
        Path.home() / ".local" / "bin" / "claude.exe",
        Path.home() / ".local" / "bin" / "claude",
        Path.home() / ".claude" / "local" / "claude",
    ):
        if candidate.exists():
            return str(candidate)
    return None


def _split_messages(messages: Sequence[Message]) -> tuple[str, str]:
    """Return (system_prompt, prompt) built from an OpenAI-style history."""
    system_parts: List[str] = []
    turns: List[tuple[str, str]] = []
    for m in messages:
        text = m.text if hasattr(m, "text") else (m.content or "")
        if not text:
            continue
        if m.role == Role.SYSTEM:
            system_parts.append(text)
        elif m.role == Role.USER:
            turns.append(("Usuario", text))
        elif m.role == Role.ASSISTANT:
            turns.append(("Asistente", text))
        elif m.role == Role.TOOL:
            turns.append(("Resultado de herramienta", text))

    system = "\n\n".join(system_parts).strip()
    if not turns:
        return system, ""
    if len(turns) == 1:
        return system, turns[0][1]

    *history, last = turns
    transcript = "\n\n".join(f"{who}: {text}" for who, text in history)
    prompt = (
        "Conversación previa (para contexto):\n"
        "<historial>\n"
        f"{transcript}\n"
        "</historial>\n\n"
        "Responde ahora al último mensaje del usuario:\n"
        f"{last[1]}"
    )
    return system, prompt


@EngineRegistry.register("claude_code")
class ClaudeCodeEngine(InferenceEngine):
    """Inference through the locally installed Claude Code CLI (headless)."""

    engine_id = "claude_code"
    is_cloud = False

    def __init__(self) -> None:
        self._cli = _find_cli()

    # ------------------------------------------------------------------ utils
    def _alias(self, model: str) -> str:
        alias = model[len(MODEL_PREFIX):] if model.startswith(MODEL_PREFIX) else model
        return alias or "sonnet"

    def _command(self, model: str, system_file: Optional[str]) -> List[str]:
        if not self._cli:
            raise RuntimeError(
                "No se encuentra Claude Code. Instálalo e inicia sesión con `claude`."
            )
        cmd = [
            self._cli,
            "-p",
            "--output-format", "stream-json",
            "--include-partial-messages",
            "--verbose",
            "--model", self._alias(model),
            "--tools", "",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--no-session-persistence",
        ]
        if system_file:
            cmd += ["--system-prompt-file", system_file]
        return cmd

    def _env(self) -> Dict[str, str]:
        env = dict(os.environ)
        # Siempre la sesión de la suscripción, nunca una clave de API facturable.
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("CLAUDE_CODE_USE_BEDROCK", None)
        env.pop("CLAUDE_CODE_USE_VERTEX", None)
        return env

    def _events(self, messages: Sequence[Message], model: str) -> Iterator[Dict[str, Any]]:
        """Run the CLI and yield its stream-json events (blocking)."""
        system, prompt = _split_messages(messages)
        if not prompt:
            return
        _SANDBOX.mkdir(parents=True, exist_ok=True)

        system_file: Optional[str] = None
        if system:
            fd, system_file = tempfile.mkstemp(prefix="oj-cc-system-", suffix=".txt")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(system)

        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        # stderr a un archivo temporal: una tubería sin leer podría llenarse y
        # bloquear el proceso mientras leemos stdout.
        errfile = tempfile.TemporaryFile()
        proc = subprocess.Popen(
            self._command(model, system_file),
            cwd=str(_SANDBOX),
            env=self._env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=errfile,
            creationflags=flags,
        )
        timer = threading.Timer(_TIMEOUT_S, proc.kill)
        timer.start()
        try:
            assert proc.stdin and proc.stdout
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.close()
            for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("{"):
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
            proc.wait()
            if proc.returncode not in (0, None):
                errfile.seek(0)
                err = errfile.read().decode("utf-8", errors="replace").strip()
                raise RuntimeError(
                    f"Claude Code terminó con código {proc.returncode}: {err[:400]}"
                )
        finally:
            timer.cancel()
            if proc.poll() is None:
                proc.kill()
            errfile.close()
            if system_file:
                try:
                    os.unlink(system_file)
                except OSError:
                    pass

    @staticmethod
    def _text_delta(event: Dict[str, Any]) -> Optional[str]:
        if event.get("type") != "stream_event":
            return None
        ev = event.get("event") or {}
        if ev.get("type") != "content_block_delta":
            return None
        delta = ev.get("delta") or {}
        if delta.get("type") == "text_delta":
            return delta.get("text") or None
        return None

    @staticmethod
    def _result_error(event: Dict[str, Any]) -> Optional[str]:
        if event.get("type") == "result" and event.get("is_error"):
            return str(event.get("result") or event.get("subtype") or "error")
        return None

    # -------------------------------------------------------------- interface
    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        parts: List[str] = []
        usage: Dict[str, Any] = {}
        final: Optional[str] = None
        for event in self._events(messages, model):
            text = self._text_delta(event)
            if text:
                parts.append(text)
            err = self._result_error(event)
            if err:
                raise RuntimeError(f"Claude Code: {err}")
            if event.get("type") == "result":
                final = event.get("result")
                usage = event.get("usage") or {}
        content = "".join(parts) or (final or "")
        prompt_tokens = int(usage.get("input_tokens") or estimate_prompt_tokens(messages))
        completion_tokens = int(usage.get("output_tokens") or max(1, len(content) // 4))
        return {
            "content": content,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "model": model,
            "finish_reason": "stop",
        }

    async def stream(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        done = object()

        def worker() -> None:
            try:
                for event in self._events(messages, model):
                    text = self._text_delta(event)
                    if text:
                        loop.call_soon_threadsafe(queue.put_nowait, text)
                    err = self._result_error(event)
                    if err:
                        raise RuntimeError(f"Claude Code: {err}")
            except BaseException as exc:  # noqa: BLE001 — se reenvía al consumidor
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, done)

        threading.Thread(target=worker, name="claude-code-stream", daemon=True).start()
        while True:
            item = await queue.get()
            if item is done:
                return
            if isinstance(item, BaseException):
                raise item
            yield item

    def list_models(self) -> List[str]:
        return [f"{MODEL_PREFIX}{a}" for a in _ALIASES] if self._cli else []

    def health(self) -> bool:
        return self._cli is not None

    def can_serve(self, model: str) -> bool:
        return model.startswith(MODEL_PREFIX)


__all__ = ["ClaudeCodeEngine", "MODEL_PREFIX"]
