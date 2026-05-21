# --- System/neuroanatomy/cortical/mirror_neurons/resonance.py ---
import json
from pathlib import Path
from typing import Dict
from System.neuroanatomy.cortical.mirror_neurons.style_parser import CorticalStyleParser


class SynapticResonanceMatrix:
    """Manages constant-time empathy compatibility lookups with bounded FIFO memory ceilings."""

    def __init__(self, style_path: Path, cache_ref: Dict[int, float]) -> None:
        self.style_path = style_path
        self._resonance_cache = cache_ref

    def calculate_empathy_resonance(
        self, sample_text: str, mode: str = "code"
    ) -> float:
        """Determines syntactic styling resonance coefficients using standard library caches."""
        text_hash = hash(sample_text)
        if text_hash in self._resonance_cache:
            return self._resonance_cache[text_hash]

        if not self.style_path.exists():
            return 0.0

        try:
            with open(self.style_path, "r", encoding="utf-8") as f:
                fp = json.load(f)
        except Exception:
            return 0.0

        if len(self._resonance_cache) >= 2000:
            for _ in range(500):
                if self._resonance_cache:
                    oldest_key = next(iter(self._resonance_cache))
                    self._resonance_cache.pop(oldest_key, None)

        observed = CorticalStyleParser.parse_metrics_isolated(sample_text, mode=mode)
        matches = 0
        total_keys = 0

        group = "code_conventions" if mode == "code" else "prose_cadence"
        if isinstance(fp, dict) and group in fp and group in observed:
            fp_group = fp[group]
            if isinstance(fp_group, dict):
                for k in observed[group]:
                    total_keys += 1
                    if fp_group.get(k) == observed[group][k]:
                        matches += 1

        if total_keys == 0:
            return 0.0

        score = round((matches / total_keys) * 0.5, 2)
        self._resonance_cache[text_hash] = score
        return score
