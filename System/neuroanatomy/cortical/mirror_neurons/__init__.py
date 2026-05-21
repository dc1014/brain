# --- System/neuroanatomy/cortical/mirror_neurons/__init__.py ---
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, cast
from System.core.paths import ROOT_DIR
from System.neuroanatomy.cortical.mirror_neurons.style_parser import CorticalStyleParser
from System.neuroanatomy.cortical.mirror_neurons.motor_tracks import (
    MotorTrackInterception,
)
from System.neuroanatomy.cortical.mirror_neurons.momentum_manager import (
    AllostaticMomentumManager,
    _STYLE_MUTEX,
)
from System.neuroanatomy.cortical.mirror_neurons.resonance_matrix import (
    SynapticResonanceMatrix,
)


class MirrorNeurons:
    """Cortical Mirror Neurons Subsystem Facade Orchestrator.

    Composes decoupled structural style engines to handle operational playback, allostatic load managers,
    and fast multi-tier token stream lexing under absolute backward-compatibility invariants.
    """

    def __init__(self, observation_vault: Optional[str] = None) -> None:
        self.vault_path = observation_vault or str(ROOT_DIR)
        sanitized_vault = str(Path(self.vault_path)).replace("\\", "/")
        self.log_path = Path(sanitized_vault) / "Meta" / "mirror_observations.jsonl"
        self.style_path = (
            Path(sanitized_vault) / "System" / "config" / "stylistic_fingerprint.json"
        )
        self.engram_path = (
            Path(sanitized_vault) / "System" / "config" / "long_term_engram.json"
        )

        # Sub-component composite orchestration bindings matching your preferred files
        self._tracks = MotorTrackInterception(self.log_path)
        self._momentum = AllostaticMomentumManager(
            self.style_path, self.engram_path, self.vault_path
        )
        self._resonance_cache: Dict[int, float] = {}
        self._resonance = SynapticResonanceMatrix(
            self.style_path, self._resonance_cache
        )

        # SYNAPTIC BRIDGE BOOTSTRAP: Seed layout settings if engram nodes exist
        if not self.style_path.exists() and self.engram_path.exists():
            try:
                with open(self.engram_path, "r", encoding="utf-8") as f:
                    engram_data = json.load(f)
                if isinstance(engram_data, dict) and "code_conventions" in engram_data:
                    self.style_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.style_path, "w", encoding="utf-8") as f:
                        json.dump(engram_data, f, indent=2)
            except Exception:
                pass

    def observe_and_record(
        self, agent_id: str, objective: str, successful_steps: List[str]
    ) -> None:
        self._tracks.observe_and_record(agent_id, objective, successful_steps)

    def synchronize_muscle_memory(self, prompt: str) -> Optional[List[str]]:
        return self._tracks.synchronize_muscle_memory(prompt)

    def _parse_metrics_isolated(
        self, sample_text: str, mode: str = "code"
    ) -> Dict[str, Any]:
        return CorticalStyleParser.parse_metrics_isolated(sample_text, mode)

    def analyze_and_mirror_style(self, sample_text: str, mode: str = "code") -> None:
        self._momentum.analyze_and_mirror_style(sample_text, mode, _STYLE_MUTEX)

    def consolidate_stylistic_baseline(self) -> None:
        self._momentum.consolidate_stylistic_baseline(_STYLE_MUTEX)
        self._resonance_cache.clear()

    def calculate_empathy_resonance(
        self, sample_text: str, mode: str = "code"
    ) -> float:
        return self._resonance.calculate_empathy_resonance(sample_text, mode)

    def inject_stylistic_prompt_context(
        self, domain_or_path: Optional[str] = None
    ) -> str:
        """Returns a string block describing your structural style to steer model outputs flawlessly."""
        base_fingerprint: Dict[str, Any] = {
            "code_conventions": {
                "indentation": "4-spaces",
                "naming": "snake_case",
                "docstrings": False,
            },
            "prose_cadence": {
                "bullet_style": "-",
                "nested_indentation": "4-spaces",
                "bold_preference": "asterisks",
                "italics_preference": "asterisks",
                "tone": "technical",
            },
        }

        if self.style_path.exists():
            try:
                with open(self.style_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        base_fingerprint = loaded
            except Exception:
                pass

        if domain_or_path:
            target_path = (
                Path(self.vault_path) / domain_or_path
                if not os.path.isabs(str(domain_or_path))
                else Path(str(domain_or_path))
            )
            sample_file: Optional[Path] = None

            if target_path.exists():
                if target_path.is_file() and target_path.suffix in (".py", ".md"):
                    sample_file = target_path
                elif target_path.is_dir():
                    valid_files = sorted(
                        [
                            p
                            for p in target_path.rglob("*")
                            if p.is_file() and p.suffix in (".py", ".md")
                        ],
                        key=lambda p: p.stat().st_mtime,
                        reverse=True,
                    )
                    if valid_files:
                        sample_file = valid_files[0]

            if sample_file:
                try:
                    content = sample_file.read_text(encoding="utf-8")
                    mode = "code" if sample_file.suffix == ".py" else "prose"
                    local_metrics = CorticalStyleParser.parse_metrics_isolated(
                        content, mode=mode
                    )

                    cc_target = base_fingerprint.get("code_conventions")
                    pc_target = base_fingerprint.get("prose_cadence")
                    if isinstance(cc_target, dict) and mode == "code":
                        cast(Dict[str, Any], cc_target).update(
                            local_metrics["code_conventions"]
                        )
                    if isinstance(pc_target, dict) and mode == "prose":
                        cast(Dict[str, Any], pc_target).update(
                            local_metrics["prose_cadence"]
                        )
                except Exception:
                    pass

        cc_final = base_fingerprint.get("code_conventions")
        pc_final = base_fingerprint.get("prose_cadence")

        cc = cast(
            Dict[str, Any],
            cc_final
            if isinstance(cc_final, dict)
            else base_fingerprint["code_conventions"],
        )
        pc = cast(
            Dict[str, Any],
            pc_final
            if isinstance(pc_final, dict)
            else base_fingerprint["prose_cadence"],
        )

        return (
            f"\n[STRICT MIRROR STYLE OVERRIDE]\n"
            f"- Code Indentation Layout: {cc.get('indentation')}\n"
            f"- Function Naming System: {cc.get('naming')}\n"
            f"- Mandatory Docstring Signatures: {cc.get('docstrings')}\n"
            f"- Text Formatting Preference: Bullet type '{pc.get('bullet_style')}' with a {pc.get('tone')} cadence.\n"
            f"- Nested Indentation Standard: {pc.get('nested_indentation')}\n"
            f"- Bold Formatting Syntactic Element: {pc.get('bold_preference')}\n"
            f"- Italics Formatting Syntactic Element: {pc.get('italics_preference')}\n"
        )
