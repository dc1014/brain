import os
import sys
from System.core.paths import ROOT_DIR


def bootstrap() -> bool:
    """⚡ THE GATEKEEPER: Hyper-fast loading hook executed on every single CLI interaction loop."""
    try:
        env_file = ROOT_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

        # Synchronize and inoculate parameters inside the secure singleton memory Vault
        from System.neuroanatomy.systemic.immune_system import vault

        vault.secure_environment()

        # ⚡ SHIFT-LEFT PERFORMANCE: Reduce 7 filesystem stat calls to 1 by checking a primary anchor
        target_dirs = [
            "Studio",
            "Personal",
            "Professional",
            "Meta",
            "Sense",
            "System/tools/engrams",
            "System/logs",
        ]
        if not (ROOT_DIR / "Meta").exists():
            for d in target_dirs:
                (ROOT_DIR / d).mkdir(parents=True, exist_ok=True)

        return True
    except Exception as e:
        print(
            f"Catastrophic Operating System Bootstrap Rejection: {e}", file=sys.stderr
        )
        return False
