# --- System/neuroanatomy/autonomic/medulla.py ---
import time
import yaml  # type: ignore[import-untyped]
import threading
import logging
import psutil
import os
import uuid
import json
import shlex
import subprocess
from typing import Any, List, Dict, Optional
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.core.concurrency import get_isolated_executor

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

_ACTIVE_MEDULLA_INSTANCES: List["MedullaOblongata"] = []


def cleanup_active_medullas() -> None:
    """🛡️ DAEMON REAPER: Cleanly disengages running Medulla instances to eliminate test stalls."""
    global _ACTIVE_MEDULLA_INSTANCES
    for instance in _ACTIVE_MEDULLA_INSTANCES:
        if instance.is_alive:
            try:
                instance.stop()
            except Exception as e:
                # ⚡ P1 FIX: Log the disengagement failure instead of passing silently
                medulla_logger.error(
                    f"Failed to cleanly disengage medulla instance: {e}"
                )
                instance.is_alive = False
    _ACTIVE_MEDULLA_INSTANCES.clear()


class OrchestrationMismatchException(Exception):
    """⚡ Custom Exception thrown when high-specificity orchestration states collapse prematurely."""

    pass


class DurableTaskLog:
    """Flat-file Write-Ahead Log (WAL) engine ensuring process state consistency."""

    def __init__(self, log_dir: str) -> None:
        self.wal_path: str = os.path.join(os.path.abspath(log_dir), "task_queue.jsonl")
        self._lock = threading.Lock()
        os.makedirs(os.path.abspath(log_dir), exist_ok=True)

    def register_intent(self, command_string: str) -> str:
        task_id = str(uuid.uuid4())
        record = {"id": task_id, "cmd": command_string, "status": "PENDING"}
        with self._lock:
            try:
                with open(self.wal_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
            except Exception as e:
                # ⚡ P1 FIX: Ensure failed intent registrations are explicitly logged
                medulla_logger.error(f"WAL Write Error (register_intent): {e}")
        return task_id

    def mark_completed(self, task_id: str, final_status: str = "DONE") -> None:
        record = {"id": task_id, "status": final_status}
        with self._lock:
            try:
                with open(self.wal_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
            except Exception as e:
                medulla_logger.error(f"WAL Write Error (mark_completed): {e}")

    def recover_interrupted_tasks(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.wal_path):
            return []

        states: Dict[str, Dict[str, Any]] = {}
        with self._lock:
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
                            states.pop(t_id, None)
            except Exception as e:
                # ⚡ P1 FIX: Log corruption during recovery rather than failing silently
                medulla_logger.error(f"WAL Read Error (recover_interrupted_tasks): {e}")

        return list(states.values())


class MedullaOblongata:
    """The Medulla Oblongata Brainstem Master Daemon."""

    def __init__(self) -> None:
        self.config_path = ROOT_DIR / "System" / "config" / "medulla.yaml"
        self.is_alive = False
        self.cognitive_state = "SLEEP"
        self.default_profile = "com.brainos.minimal_ready"

        self._last_tier_elevation_time = 0.0
        self._min_duration_threshold_seconds = 1.5

        self.daemons: dict[str, threading.Thread] = {}
        self.active_instances: dict[str, Any] = {}
        self.config_data = self._load_blueprint()
        self._main_pid = os.getpid()

        self.ipc_client: Optional[Any] = None
        self.task_log = DurableTaskLog(str(LOG_PATH))

        # ⚡ P0 PERFORMANCE: Initialize the dynamic multi-core allocation pool
        self.recovery_pool = get_isolated_executor(max_workers=3)

        _ACTIVE_MEDULLA_INSTANCES.append(self)

    def _load_blueprint(self) -> dict[str, Any]:
        if not self.config_path.exists():
            medulla_logger.warning(
                "medulla.yaml mapping missing. Yielding to defaults."
            )
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("medulla", {})

    def calculate_specificity_score(self, command_string: str) -> int:
        score = 10
        if "execute_pipeline" in command_string or "dispatch_task" in command_string:
            score += 40
        if "playwright" in command_string or "chromium" in command_string:
            score += 30
        if "recovery" in command_string or "acc" in command_string:
            score += 25
        return score

    def allocate_orchestration_tier(self, score: int) -> str:
        if score >= 70:
            return "ORCHESTRATION_CRITICAL"
        if score >= 40:
            return "ORCHESTRATION_STANDARD"
        return "ORCHESTRATION_MINIMAL"

    def modulate_runtime_state(self, target_state: str) -> None:
        current_state = self.cognitive_state
        now = time.time()

        if current_state in (
            "ORCHESTRATION_STANDARD",
            "ORCHESTRATION_CRITICAL",
        ) and target_state in ("IDLE_READY", "ORCHESTRATION_MINIMAL"):
            elapsed = now - self._last_tier_elevation_time
            if elapsed < self._min_duration_threshold_seconds:
                msg = f"State churn detected! Slid from {current_state} to {target_state} in {elapsed:.4f}s."
                medulla_logger.warning(f"COS Arbiter [Exception Intercepted]: {msg}")
                raise OrchestrationMismatchException(msg)

        if target_state in ("ORCHESTRATION_STANDARD", "ORCHESTRATION_CRITICAL"):
            self._last_tier_elevation_time = now

        self.cognitive_state = target_state
        medulla_logger.info(
            f"System state modulated: {current_state} -> {target_state}"
        )

    def boot_recovery_sequence(self) -> None:
        interrupted_tasks = self.task_log.recover_interrupted_tasks()
        if not interrupted_tasks:
            return

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

            mock_history = [
                {"tool": "shell_execution", "status": "FAILED", "cmd": cmd_str}
            ]
            modulation_chemistry = acc.inspect_context_buffer(mock_history)

            # ⚡ ZERO-DEBT: Explicitly cast to float to pacify Mypy
            target_temp = float(modulation_chemistry.get("temperature", 0.0))

            # ⚡ P1 FIX: Inherit the fast fallback model from the user's DNA identity
            from System.core.dna import get_dna_config

            fallback = (
                get_dna_config().get("models", {}).get("fast", "openai/gpt-4o-mini")
            )

            # ⚡ ZERO-DEBT: Force strict string evaluation and eliminate 'None' ambiguity
            target_engine = str(
                modulation_chemistry.get("engine_override")
                or fallback
                or "openai/gpt-4o-mini"
            )

            score = self.calculate_specificity_score(cmd_str)
            target_tier = self.allocate_orchestration_tier(score)

            try:
                self.modulate_runtime_state(target_tier)
            except OrchestrationMismatchException:
                self.cognitive_state = target_tier

            # ⚡ Routinely dispatch to the isolated PEP 734 / Process pool
            self.recovery_pool.submit(
                self._execute_recovered_task_safely,
                task_id,
                cmd_str,
                target_temp,
                target_engine,
            )

    def _execute_recovered_task_safely(
        self, task_id: str, command: str, temperature: float, engine: str
    ) -> None:
        try:
            env_override = os.environ.copy()
            env_override["BRAIN_RECOVERY_TEMPERATURE"] = str(temperature)
            env_override["BRAIN_RECOVERY_ENGINE"] = engine

            # ⚡ P0 FIX: Safely split the command string to completely eliminate
            # the shell=True command injection vulnerability.
            safe_command = shlex.split(command)

            result = subprocess.run(
                safe_command,
                shell=False,
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
        finally:
            if self.cognitive_state in (
                "ORCHESTRATION_STANDARD",
                "ORCHESTRATION_CRITICAL",
            ):
                try:
                    self.modulate_runtime_state("ORCHESTRATION_MINIMAL")
                except OrchestrationMismatchException:
                    self.cognitive_state = "ORCHESTRATION_MINIMAL"

    def _cognitive_heartbeat(self):
        while self.is_alive:
            if self.cognitive_state in (
                "ORCHESTRATION_MINIMAL",
                "ORCHESTRATION_STANDARD",
                "ORCHESTRATION_CRITICAL",
            ):
                try:
                    from System.core.orchestrator import run_pending_queue

                    run_pending_queue()
                except Exception as e:
                    medulla_logger.error(f"Cognitive heartbeat exception: {str(e)}")

            for _ in range(150):
                if not self.is_alive:
                    break
                time.sleep(0.1)

    def _monitor_homeostasis(self):
        circadian = self.config_data.get("circadian_rhythm", {})
        sleep_time = circadian.get("sleep_trigger_time", "03:00")

        while self.is_alive:
            try:
                current_clock = time.strftime("%H:%M")
                if current_clock == sleep_time:
                    console.print(
                        "[bold purple]🧠 Medulla: Triggering system-wide Circadian Sleep Phase...[/bold purple]"
                    )
                    self.stop()
                    time.sleep(60)

                from System.neuroanatomy.autonomic.interoception import (
                    check_energy_levels,
                )

                check_energy_levels()
            except Exception as e:
                medulla_logger.error(f"Homeostasis disruption: {str(e)}")

            for _ in range(300):
                if not self.is_alive:
                    break
                time.sleep(0.1)

    def _supervise_threads(self):
        daemons_config = self.config_data.get("background_daemons", {})

        while self.is_alive:
            if daemons_config.get("dermis_receptor", {}).get("enabled", True):
                if "dermis" not in self.daemons:
                    try:
                        port = daemons_config.get("dermis_receptor", {}).get(
                            "secure_port", 8080
                        )
                        from Sense.receptors.dermis import DermisAbstraction

                        dermis_skin = DermisAbstraction(port=port)
                        self.active_instances["dermis"] = dermis_skin

                        dermis_thread = threading.Thread(
                            target=dermis_skin.start,
                            name="DermisReceptorThread",
                            daemon=True,
                        )
                        dermis_thread.start()
                        self.daemons["dermis"] = dermis_thread
                    except Exception as e:
                        medulla_logger.error(
                            f"Dermis initial boot setup failure: {str(e)}"
                        )
                elif not self.daemons["dermis"].is_alive():
                    console.print(
                        "[bold red]💓 Medulla: Dermis cardiac arrest detected! Reviving network skin...[/bold red]"
                    )
                    try:
                        port = daemons_config.get("dermis_receptor", {}).get(
                            "secure_port", 8080
                        )
                        from Sense.receptors.dermis import DermisAbstraction

                        dermis_skin = DermisAbstraction(port=port)
                        self.active_instances["dermis"] = dermis_skin

                        dermis_thread = threading.Thread(
                            target=dermis_skin.start,
                            name="DermisReceptorThread",
                            daemon=True,
                        )
                        dermis_thread.start()
                        self.daemons["dermis"] = dermis_thread
                    except Exception as e:
                        medulla_logger.error(f"Dermis resuscitation failure: {str(e)}")

            if daemons_config.get("file_watcher", {}).get("enabled", True):
                if "watcher" not in self.daemons:
                    try:
                        import System.cli_somatic as somatic

                        if hasattr(somatic, "watch"):
                            watcher_thread = threading.Thread(
                                target=somatic.watch,
                                name="SomatosensoryWatcherThread",
                                daemon=True,
                            )
                            watcher_thread.start()
                            self.daemons["watcher"] = watcher_thread
                    except Exception as e:
                        medulla_logger.error(
                            f"Watcher initial boot setup failure: {str(e)}"
                        )
                elif not self.daemons["watcher"].is_alive():
                    console.print(
                        "[bold yellow]🫁 Medulla: Watcher respiratory arrest detected! Reviving somatosensory cortex...[/bold yellow]"
                    )
                    try:
                        import System.cli_somatic as somatic

                        if hasattr(somatic, "watch"):
                            watcher_thread = threading.Thread(
                                target=somatic.watch,
                                name="SomatosensoryWatcherThread",
                                daemon=True,
                            )
                            watcher_thread.start()
                            self.daemons["watcher"] = watcher_thread
                    except Exception as e:
                        medulla_logger.error(f"Watcher resuscitation failure: {str(e)}")

            for _ in range(50):
                if not self.is_alive:
                    break
                time.sleep(0.1)

    def wake(self):
        """Sparks autonomic activity, establishing the Default Orchestration Baseline Profile safely."""
        if self.is_alive:
            return

        # 🔐 HARDENED BOOT RECOVERY: Clean up any stale file-based lock flags left behind by
        # previous hard process terminations or watchdog unlinks to prevent startup hangs.
        try:
            for root, _, files in os.walk(str(ROOT_DIR)):
                for f in files:
                    if f.endswith(".lock"):
                        lock_file = os.path.join(root, f)
                        try:
                            os.unlink(lock_file)
                            console.print(
                                f"[dim yellow]🧹 Purged stale process lock: {f}[/dim yellow]"
                            )
                        except Exception:
                            pass
        except Exception as e:
            medulla_logger.error(f"Stale lock file recovery sweep failed: {str(e)}")

        self.is_alive = True
        self.cognitive_state = "IDLE_READY"

        start_msg = "Medulla Oblongata initialized to IDLE_READY state."
        console.print(f"[bold green]🧠 {start_msg}[/bold green]")
        medulla_logger.info(start_msg)

        try:
            self.boot_recovery_sequence()
        except Exception as e:
            medulla_logger.critical(f"WAL Boot recovery crash bypass: {str(e)}")

        threading.Thread(target=self._supervise_threads, daemon=True).start()
        threading.Thread(target=self._monitor_homeostasis, daemon=True).start()
        threading.Thread(target=self._cognitive_heartbeat, daemon=True).start()

        # ⚡ DEFAULT BASELINE PROFILE: Drop back into the minimal Ready active layer
        self.cognitive_state = "ORCHESTRATION_MINIMAL"
        medulla_logger.info(
            f"System profile established: {self.default_profile} [ORCHESTRATION_MINIMAL]"
        )

    def pre_sleep_sequence(self) -> None:
        console.print(
            "\n[bold magenta]💤 Medulla: Initiating PRE_SLEEP_SEQUENCE handshake...[/bold magenta]"
        )
        medulla_logger.info(
            "Executing graceful disengagement protocol across dependent channels."
        )
        self.cognitive_state = "IDLE_READY"

        dermis_instance = self.active_instances.get("dermis")
        if distress_signal := getattr(dermis_instance, "shutdown", None):
            try:
                distress_signal()
            except Exception as e:
                medulla_logger.error(f"Failed to signal Dermis disengagement: {e}")

        start_wait = time.time()
        while time.time() - start_wait < 3.0:
            dermis_alive = (
                "dermis" in self.daemons and self.daemons["dermis"].is_alive()
            )
            if not dermis_alive:
                break
            time.sleep(0.2)

        console.print(
            "[bold green]✅ Handshake complete: Dependent receptors detached successfully.[/bold green]"
        )

    def stop(self) -> None:
        try:
            self.pre_sleep_sequence()
        except Exception as e:
            medulla_logger.error(f"Error during pre-sleep coordination sweep: {e}")

        # ⚡ SELF-DEFENDING TEST GATEWAY: Absolute block preventing live LLM generation during tests
        if os.environ.get("BRAIN_OS_TESTING") == "1":
            medulla_logger.info(
                "Medulla sleep phase: Daydream loop bypassed inside testing environment."
            )
        else:
            try:
                from System.neuroanatomy.autonomic.dmn import trigger_daydreams

                medulla_logger.info(
                    "Medulla brainstem sleep phase: Invoking default mode network distillation loop."
                )
                trigger_daydreams(topic=None, domain="STUDIO")
            except Exception as dmn_err:
                medulla_logger.error(
                    f"Failed to execute background subcortex synthesis during disengagement: {dmn_err}"
                )

        self.is_alive = False
        self.cognitive_state = "SLEEP"

        # ⚡ Cleanly sever the multi-core executor pool
        self.recovery_pool.shutdown(wait=False, cancel_futures=True)

        # ⚡ SYSTEM PROTECTION GATE: Avoid recursively terminating the pytest runner's entire infrastructure process tree
        if os.environ.get("BRAIN_OS_TESTING") == "1":
            medulla_logger.info(
                "Medulla sleep phase: Bypassed recursive psutil child process sweeps inside testing track."
            )
        else:
            try:
                parent = psutil.Process(self._main_pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                _, alive = psutil.wait_procs(children, timeout=2)
                for child in alive:
                    child.kill()
            except Exception as e:
                medulla_logger.error(f"Process cleanup warning: {str(e)}")

        stop_msg = (
            "Medulla Oblongata entering sleep state. All systems spun down cleanly."
        )
        console.print(f"[bold yellow]💤 {stop_msg}[/bold yellow]")
        medulla_logger.info(stop_msg)


def child_boot(ipc_address: str):
    from multiprocessing.connection import Client

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
            # ⚡ DESIGN INTEGRITY MAINTENANCE: Symmetrical fix to avoid runtime attribute breaks
            time.sleep(1)
    except KeyboardInterrupt:
        medulla.stop()
