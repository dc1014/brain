import sys
import uuid
import tempfile
import os
import subprocess
import time
from typing import Any
from multiprocessing.connection import Listener
from rich.console import Console

console = Console()


class ThymusGland:
    """
    The Anti-Evil Watchdog (Parent Supervisor).
    Boots the Medulla as a child process and monitors its velocity via IPC.
    Violently severs the nervous system if the agent goes rogue.
    """

    def __init__(self) -> None:
        # ⚡ FLAW 1 FIX: Dynamic, collision-free IPC address
        pipe_id = uuid.uuid4().hex
        if sys.platform == "win32":
            self.address = rf"\\.\pipe\brain_thymus_{pipe_id}"
        else:
            self.address = os.path.join(
                tempfile.gettempdir(), f"brain_thymus_{pipe_id}.sock"
            )

        self.listener = Listener(self.address)

        # ⚡ THE FIX: Explicitly type the process so Mypy stops guessing!
        self.medulla_process: subprocess.Popen[Any] | None = None

        self.destructive_velocity_window: list[float] = []
        self.MAX_MUTATIONS = 5
        self.WINDOW_SECONDS = 10

    def boot(self) -> None:
        console.print(
            "[bold cyan]🛡️ Thymus Gland: Supervising Medulla as Parent Process...[/bold cyan]"
        )

        # ⚡ FLAW 3 FIX: Do not pipe stdout/stderr. Let it flow naturally to the terminal.
        boot_script = (
            "import sys; "
            "from System.neuroanatomy.autonomic.medulla import child_boot; "
            f"child_boot(r'{self.address}')"
        )

        self.medulla_process = subprocess.Popen([sys.executable, "-c", boot_script])
        self._monitor_loop()

    def _monitor_loop(self) -> None:
        try:
            conn = self.listener.accept()
        except Exception as e:
            console.print(f"[dim red]Thymus IPC Accept Error: {e}[/dim red]")
            return

        while True:
            # ⚡ THE FIX: Defensive checking protects against Pytest returning a NoneType mock
            if self.medulla_process and self.medulla_process.poll() is not None:
                console.print(
                    "[dim yellow]🛡️ Thymus: Medulla process terminated naturally.[/dim yellow]"
                )
                break

            # ⚡ FLAW 5 FIX: Defensive polling prevents blocking locks
            if conn.poll(timeout=1.0):
                try:
                    event = conn.recv()
                    self._analyze_event(event)
                except (EOFError, ConnectionResetError):
                    console.print(
                        "[dim yellow]🛡️ Thymus: IPC Connection closed.[/dim yellow]"
                    )
                    break

    def _analyze_event(self, event: dict) -> None:
        # ⚡ FLAW 4 FIX: Only track destructive mutations, allow rapid read operations
        if event.get("impact") != "destructive":
            return

        now = time.time()
        self.destructive_velocity_window.append(now)
        self.destructive_velocity_window = [
            t for t in self.destructive_velocity_window if now - t < self.WINDOW_SECONDS
        ]

        if len(self.destructive_velocity_window) > self.MAX_MUTATIONS:
            console.print(
                "\n[bold red]🚨 THYMUS: Rogue velocity detected! Escalating immune response![/bold red]"
            )
            self._escalate()

    def _escalate(self) -> None:
        from System.neuroanatomy.autonomic.vagus_nerve import trigger_halt
        from System.neuroanatomy.autonomic.vestibular import restore_balance

        # Level 1: Graceful Vagus Nerve Halt
        trigger_halt()

        for _ in range(5):
            if self.medulla_process and self.medulla_process.poll() is not None:
                break
            time.sleep(1)

        # Level 2: Apoptosis Kill Switch
        if self.medulla_process and self.medulla_process.poll() is None:
            console.print(
                "[bold red]💀 THYMUS: Medulla unresponsive. Executing SIGKILL.[/bold red]"
            )
            self.medulla_process.kill()

        console.print(
            "[dim yellow]⚖️ Thymus: Forcing Vestibular Rollback...[/dim yellow]"
        )
        restore_balance()
