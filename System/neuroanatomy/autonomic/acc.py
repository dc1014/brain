# --- System/neuroanatomy/autonomic/acc.py ---
import os
import yaml  # type: ignore[import-untyped]
from typing import Dict, Any, List
from System.core.paths import ROOT_DIR


class AnteriorCingulateCortex:
    """Anterior Cingulate Cortex (ACC) cognitive monitoring subsystem.

    Responsible for conflict monitoring, dynamic neuromodulation tuning,
    and triggering strategy switches when loops or logic traps are detected.
    """

    def __init__(self) -> None:
        config_path = os.path.join(ROOT_DIR, "System", "config", "acc.yaml")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config: Dict[str, Any] = yaml.safe_load(f)
        except Exception:
            # Safe defensive fallback matrix configurations if file is unreadable
            self.config = {
                "conflict_monitoring": {
                    "max_consecutive_tool_failures": 3,
                    "epistemic_drift_threshold": 0.75,
                    "sunk_cost_line_limit": 3,
                },
                "neuromodulation": {
                    "high_stress": {
                        "temperature": 0.0,
                        "engine_override": "claude-3-5-sonnet",
                    },
                    "low_stress": {"temperature": 0.7, "engine_override": "local-slm"},
                },
                "fallacy_patterns": [
                    r"(?i)confirming without checking",
                    r"(?i)repeating identical execution",
                ],
            }
        self.tension_score: float = 0.0

    def inspect_context_buffer(
        self, interaction_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Scans recent ledger streams for logical fallacies or stuck loops.

        Args:
            interaction_history: A list of recent event dictionaries tracking tool statuses.

        Returns:
            A dictionary specifying parameter adjustments or required structural action shifts.
        """
        consecutive_failures = 0
        last_tool = None

        for event in reversed(interaction_history):
            if event.get("status") == "FAILED":
                if last_tool is None or event.get("tool") == last_tool:
                    consecutive_failures += 1
                last_tool = event.get("tool")
            else:
                break

        max_failures: int = self.config["conflict_monitoring"][
            "max_consecutive_tool_failures"
        ]
        if consecutive_failures >= max_failures:
            return self.trigger_circuit_breaker()

        return self.modulate_chemistry(consecutive_failures)

    def modulate_chemistry(self, failures: int) -> Dict[str, Any]:
        """Returns runtime parameters modified dynamically based on environmental tension layers.

        Args:
            failures: Total count of sequential failures identified.

        Returns:
            A dictionary containing neuromodulatory parameter overrides.
        """
        if failures > 0:
            max_fail = float(
                self.config["conflict_monitoring"]["max_consecutive_tool_failures"]
            )
            self.tension_score = min(1.0, failures / max_fail)
            return dict(self.config["neuromodulation"]["high_stress"])

        self.tension_score = 0.0
        return dict(self.config["neuromodulation"]["low_stress"])

    def trigger_circuit_breaker(self) -> Dict[str, Any]:
        """Forces immediate topology alteration to bypass computational gridlock conditions."""
        self.tension_score = 1.0
        return {
            "action": "FORCE_STRATEGY_SHIFT",
            "clear_context": True,
            "fallback_archetype": "Auditor",
        }
