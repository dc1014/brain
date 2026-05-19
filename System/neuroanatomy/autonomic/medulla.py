import time
import yaml  # type: ignore
import threading
import logging
import psutil
import os
from typing import Any
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

    def _load_blueprint(self) -> dict[str, Any]:
        if not self.config_path.exists():
            medulla_logger.warning(
                "medulla.yaml mapping missing. Yielding to defaults."
            )
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("medulla", {})

    def _cognitive_heartbeat(self):
        """Autonomously processes the pending cognitive task queue (Obsidian notes)."""
        while self.is_alive:
            try:
                from System.core.orchestrator import run_pending_queue

                # ⚡ THE FIX: Removed the broken BiologicalLock. Let it run freely!
                run_pending_queue()
            except Exception as e:
                medulla_logger.error(f"Cognitive heartbeat exception: {str(e)}")

            # Poll the queue every 15 seconds
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

                    # ⚡ THE FIX: Removed the broken BiologicalLock here too!
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
            # 🛡️ Dermis / Heartbeat Supervision
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

            # 🫁 File Watcher / Respiratory Supervision
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
