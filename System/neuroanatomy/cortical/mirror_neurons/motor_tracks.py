# --- System/neuroanatomy/cortical/mirror_neurons/tracks.py ---
import json
import time
import os
from pathlib import Path
from typing import List, Optional
from System.core.locks import StateLock


class MotorTrackInterception:
    """Manages cross-agent operational logs, trajectory maps, and Hebbian trace potentiation workflows."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path

    def observe_and_record(
        self, agent_id: str, objective: str, successful_steps: List[str]
    ) -> None:
        """Logs sequence command histories natively using atomic hidden buffer swaps to avoid file gridlocks."""
        if not successful_steps:
            return

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_objective = objective.strip().lower().replace("\\", "/")
        sanitized_steps = [str(step).replace("\\", "/") for step in successful_steps]

        records: List[dict] = []
        found_existing = False

        if self.log_path.exists():
            with StateLock(str(self.log_path)):
                try:
                    with open(self.log_path, "r", encoding="utf-8") as f:
                        for line in f:
                            clean_line = line.strip()
                            if not clean_line:
                                continue
                            rec = json.loads(clean_line)
                            if rec.get("objective_slug") == normalized_objective:
                                rec["resonance_score"] = round(
                                    rec.get("resonance_score", 1.0) + 0.5, 2
                                )
                                rec["parameterized_chain"] = sanitized_steps
                                rec["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                                found_existing = True
                            records.append(rec)
                except Exception:
                    pass

        if not found_existing:
            observation_payload = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "observed_agent": str(agent_id),
                "objective_slug": normalized_objective,
                "parameterized_chain": sanitized_steps,
                "resonance_score": 1.0,
            }
            records.append(observation_payload)

        tmp_log_path = self.log_path.with_suffix(".tmp")
        with StateLock(str(self.log_path)):
            try:
                with open(tmp_log_path, "w", encoding="utf-8") as f:
                    for r in records:
                        f.write(json.dumps(r) + "\n")
                os.replace(tmp_log_path, self.log_path)
            except Exception:
                if tmp_log_path.exists():
                    try:
                        os.remove(tmp_log_path)
                    except OSError:
                        pass
                raise

    def synchronize_muscle_memory(self, prompt: str) -> Optional[List[str]]:
        """Scans consolidated trans-agent command maps to shortcut repetitive tasks."""
        if not self.log_path.exists():
            return None

        normalized_prompt = prompt.strip().lower().replace("\\", "/")
        result_chain: Optional[List[str]] = None

        with StateLock(str(self.log_path)):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        clean_line = line.strip()
                        if not clean_line:
                            continue
                        record = json.loads(clean_line)
                        if record.get("objective_slug") == normalized_prompt:
                            result_chain = list(record["parameterized_chain"])
            except Exception:
                pass

        return result_chain
