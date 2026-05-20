# --- System/neuroanatomy/autonomic/medulla.py ---
import time
import yaml  # type: ignore[import-untyped]
import threading
import logging
import psutil
import os
import uuid
import json
import subprocess
from typing import Any, List, Dict
from rich.console import Console

from System.core.paths import ROOT_DIR
from Sense.receptors.dermis import Dermis

console = Console()
LOG_PATH = ROOT_DIR / "System" / "logs"
LOG_PATH.mkdir(parents=True, exist_ok=True)

medulla_logger = logging.getLogger("Medulla")
medulla_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_PATH / "medulla.log", encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
if not medulla_logger.handlers:
    medulla_logger.addHandler(file_handler)


class DurableTaskLog:
    """Flat-file Write-Ahead Log (WAL) engine ensuring process state consistency with strict mutex locking."""

    def __init__(self, log_dir: str) -> None:
        self.wal_path: str = os.path.join(os.path.abspath(log_dir), "task_queue.jsonl")
        self._lock = (
            threading.Lock()
        )  # ⚡ THREAD MUTEX MUTATOR: Prevents state block interleaving
        os.makedirs(os.path.abspath(log_dir), exist_ok=True)

    def register_intent(self, command_string: str) -> str:
        """Logs an intent marker before running volatile scripts with synchronized multi-thread access."""
        task_id = str(uuid.uuid4())
        record = {"id": task_id, "cmd": command_string, "status": "PENDING"}
        with self._lock:  # Engage thread guard
            try:
                with open(self.wal_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
            except Exception:
                pass
        return task_id

    def mark_completed(self, task_id: str, final_status: str = "DONE") -> None:
        """Appends a completion marker to cleanly sign off log state transactions thread-safely."""
        record = {"id": task_id, "status": final_status}
        with self._lock:  # Engage thread guard
            try:
                with open(self.wal_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
            except Exception:
                pass

    def recover_interrupted_tasks(self) -> List[Dict[str, Any]]:
        """Scans state indicators on boot, flagging tasks that crashed mid-execution loop."""
        if not os.path.exists(self.wal_path):
            return []

        states: Dict[str, Dict[str, Any]] = {}
        with self._lock:  # Enforce transaction boundary isolation
            try:
                with open(self.wal_path, "r", encoding="utf-8") as f:
                    for line in f:
                        clean_line = line.strip()
                        if not clean_line:
                            continue
                        evt: Dict[str, Any] = json.loads(clean_line)
                        t_id = evt.get("id")
                        if not t_id:
                            continue

                        if evt.get("status") == "PENDING":
                            states[t_id] = evt
                        else:
                            # Balanced completion signature encountered
                            states.pop(t_id, None)
            except Exception:
                pass

        return list(states.values())


class MedullaOblongata:
    """
    The Medulla Oblongata Brainstem Master Daemon.
    Supervises involuntary system lifecycles, background daemons,
    circadian schedules, queue processing, and operational homeostasis.
    """

    def __init__(self) -> None:
        self.config_path = ROOT_DIR / "System" / "config" / "medulla.yaml"
        self.is_alive = False
        self.daemons: dict[str, threading.Thread] = {}
        self.config_data = self._load_blueprint()
        self._main_pid = os.getpid()
        self.ipc_client: Any = None

        # BIND DURABLE TASK LOG NATIVELY: Point directly to our sanitized logs path
        self.task_log = DurableTaskLog(str(LOG_PATH))

    def _load_blueprint(self) -> dict[str, Any]:
        if not self.config_path.exists():
            medulla_logger.warning(
                "medulla.yaml mapping missing. Yielding to defaults."
            )
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("medulla", {})

    def boot_recovery_sequence(self) -> None:
        """Sweeps Write-Ahead Logs on boot and modulates recovery settings through the ACC."""
        interrupted_tasks = self.task_log.recover_interrupted_tasks()
        if not interrupted_tasks:
            return

        # Lazy local import to break any potential top-level pre-compile import rings cleanly
        from System.neuroanatomy.autonomic.acc import AnteriorCingulateCortex

        acc = AnteriorCingulateCortex()

        console.print(
            f"[bold purple]🫁 Medulla WAL: Found {len(interrupted_tasks)} interrupted tasks. Triggering closed-loop recovery...[/bold purple]"
        )

        for task in interrupted_tasks:
            task_id = task.get("id", "unknown")
            cmd_str = task.get("cmd", "")
            if not cmd_str:
                continue

            console.print(
                f"[bold yellow]🫁 Medulla WAL: Recovering interrupted task transaction {task_id}...[/bold yellow]"
            )
            medulla_logger.info(f"WAL Recovery triggered for task {task_id}: {cmd_str}")

            # Formulate historical error failure data to analyze stress limits through the ACC framework
            mock_history = [
                {"tool": "shell_execution", "status": "FAILED", "cmd": cmd_str}
            ]
            modulation_chemistry = acc.inspect_context_buffer(mock_history)

            # Extract modulated parameters deterministically based on stress indicators
            target_temp = modulation_chemistry.get("temperature", 0.0)
            target_engine = modulation_chemistry.get(
                "engine_override", "openai/gpt-4o-mini"
            )

            # Execute the recovered pipeline task in a secure, non-blocking background thread wrapper
            threading.Thread(
                target=self._execute_recovered_task_safely,
                args=(task_id, cmd_str, target_temp, target_engine),
                daemon=True,
            ).start()

    def _execute_recovered_task_safely(
        self, task_id: str, command: str, temperature: float, engine: str
    ) -> None:
        """Background execution engine executing resuscitated tasks under ACC context parameters."""
        try:
            # Inject neuromodulated variables smoothly into the execution context environment
            env_override = os.environ.copy()
            env_override["BRAIN_RECOVERY_TEMPERATURE"] = str(temperature)
            env_override["BRAIN_RECOVERY_ENGINE"] = str(engine)

            # Safely trigger shell execution with isolated process parameters
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                env=env_override,
                timeout=300,
            )

            if result.returncode == 0:
                self.task_log.mark_completed(task_id, "DONE")
                medulla_logger.info(
                    f"WAL Recovery successfully signed off task {task_id}."
                )
            else:
                self.task_log.mark_completed(task_id, "FAILED")
                medulla_logger.error(
                    f"WAL Recovery task execution failed for {task_id}: {result.stderr}"
                )
        except Exception as e:
            self.task_log.mark_completed(task_id, "CRASHED")
            medulla_logger.critical(
                f"WAL Recovery tracking critical system exception for {task_id}: {str(e)}"
            )

    def _cognitive_heartbeat(self):
        """Autonomously processes the pending cognitive task queue (Obsidian notes)."""
        while self.is_alive:
            try:
                queue_file = ROOT_DIR / "Meta" / "queue.jsonl"
                approved_flag = ROOT_DIR / "Meta" / ".approved"
                action_expected = queue_file.exists() and approved_flag.exists()

                from System.core.orchestrator import run_pending_queue

                run_pending_queue()

                # Send diagnostic ping to Thymus Supervisor
                if action_expected and self.ipc_client:
                    try:
                        self.ipc_client.send(
                            {
                                "type": "queue_processed",
                                "impact": "destructive",
                                "timestamp": time.time(),
                            }
                        )
                    except Exception:
                        pass
            except Exception as e:
                medulla_logger.error(f"Cognitive heartbeat exception: {str(e)}")

            time.sleep(15)

    def _monitor_homeostasis(self):
        """Metabolic Loop: Tracks internal vitals, token budgets, and circadian timing adjustments."""
        circadian = self.config_data.get("circadian_rhythm", {})
        sleep_time = circadian.get("sleep_trigger_time", "03:00")

        while self.is_alive:
            try:
                current_clock = time.strftime("%H:%M")

                if current_clock == sleep_time:
                    console.print(
                        "[bold purple]🧠 Medulla: Triggering system-wide Circadian Sleep Phase...[/bold purple]"
                    )
                    medulla_logger.info(
                        "Circadian switch activated. Invoking maintenance algorithms."
                    )
                    from System.cli_somatic import sleep

                    sleep()
                    time.sleep(60)

                from System.neuroanatomy.autonomic.interoception import (
                    check_energy_levels,
                )

                check_energy_levels()
            except Exception as e:
                medulla_logger.error(f"Homeostasis disruption: {str(e)}")

            time.sleep(30)

    def _supervise_threads(self):
        """Respiratory Loop: Monitors operational threads, automatically resuscitating crashed organs."""
        daemons_config = self.config_data.get("background_daemons", {})

        while self.is_alive:
            # Dermis / Heartbeat Supervision
            if daemons_config.get("dermis_receptor", {}).get("enabled", True):
                if (
                    "dermis" not in self.daemons
                    or not self.daemons["dermis"].is_alive()
                ):
                    console.print(
                        "[bold red]💓 Medulla: Dermis cardiac arrest detected! Reviving network skin...[/bold red]"
                    )
                    medulla_logger.error(
                        "Dermis thread collapsed. Initiating automated resuscitation."
                    )
                    try:
                        port = daemons_config.get("dermis_receptor", {}).get(
                            "secure_port", 8080
                        )
                        dermis_skin = Dermis(port=port)
                        dermis_skin.start()
                        if dermis_skin.server:
                            self.daemons["dermis"] = threading.current_thread()
                    except Exception as e:
                        medulla_logger.error(f"Dermis resuscitation failure: {str(e)}")

            # File Watcher / Respiratory Supervision
            if daemons_config.get("file_watcher", {}).get("enabled", True):
                if (
                    "watcher" not in self.daemons
                    or not self.daemons["watcher"].is_alive()
                ):
                    console.print(
                        "[bold yellow]🫁 Medulla: Watcher respiratory arrest detected! Reviving somatosensory cortex...[/bold yellow]"
                    )
                    medulla_logger.error(
                        "File watcher thread collapsed. Reviving filesystem observer."
                    )
                    try:
                        import System.cli_somatic as somatic

                        if hasattr(somatic, "watch"):
                            watcher_thread = threading.Thread(
                                target=somatic.watch, daemon=True
                            )
                            watcher_thread.start()
                            self.daemons["watcher"] = watcher_thread
                    except Exception as e:
                        medulla_logger.error(f"Watcher resuscitation failure: {str(e)}")

            time.sleep(5)

    def wake(self):
        """Sparks autonomic activity within the master daemon pools."""
        if self.is_alive:
            return
        self.is_alive = True

        start_msg = (
            "Medulla Oblongata fully awake. Core daemon orchestration loops active."
        )
        console.print(f"[bold green]🧠 {start_msg}[/bold green]")
        medulla_logger.info(start_msg)

        # ⚡ EXECUTE DURABLE RECOVERY TRANSACTION SWEEP: Scan and restore crashed intents thread-safely upon boot
        try:
            self.boot_recovery_sequence()
        except Exception as e:
            medulla_logger.critical(f"WAL Boot recovery crash bypass: {str(e)}")

        threading.Thread(target=self._supervise_threads, daemon=True).start()
        threading.Thread(target=self._monitor_homeostasis, daemon=True).start()
        threading.Thread(target=self._cognitive_heartbeat, daemon=True).start()

        daemons_config = self.config_data.get("background_daemons", {})
        if daemons_config.get("dermis_receptor", {}).get("auto_tunnel_on_wake", False):
            try:
                import System.cli_somatic as somatic

                threading.Thread(target=somatic.expose_dermis, daemon=True).start()
            except Exception:
                pass

    def stop(self):
        """Retracts neural processing loops cleanly and hunts down orphaned OS processes."""
        self.is_alive = False

        try:
            parent = psutil.Process(self._main_pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            _, alive = psutil.wait_procs(children, timeout=3)
            for child in alive:
                child.kill()
        except Exception as e:
            medulla_logger.error(f"Process cleanup warning: {str(e)}")

        stop_msg = (
            "Medulla Oblongata entering sleep state. Core daemons spun down cleanly."
        )
        console.print(f"[bold yellow]💤 {stop_msg}[/bold yellow]")
        medulla_logger.info(stop_msg)


def child_boot(ipc_address: str):
    """Bootloader for the Thymus to spawn the Medulla as a secure subprocess."""
    from multiprocessing.connection import Client
    import time

    client = None
    try:
        client = Client(ipc_address)
    except Exception:
        pass

    medulla = MedullaOblongata()
    medulla.ipc_client = client
    medulla.wake()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        medulla.stop()
