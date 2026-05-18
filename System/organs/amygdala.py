import re

# --- SHIFT-LEFT SECURITY: Background Threat Signatures ---
FORBIDDEN_BACKGROUND_COMMANDS = [
    r"\bcurl\b",
    r"\bwget\b",
    r"\bnc\b",
    r"\bnetcat\b",
    r"\bmkfifo\b",
    r"\bbash\s+-i\b",
    r"\bpowershell\s+-e\b",
    r"\brm\s+-rf\b",
]


def scan_prompt(prompt: str) -> tuple[bool, str]:
    """
    The Amygdala: Shift-Left Threat Detection.
    A biological reflex arc that processes inputs before the Dispatcher
    to prevent prompt injections, malicious payloads, and catastrophic commands.
    """
    prompt_lower = prompt.lower()

    # 1. Prompt Injection Heuristics (The "Hijack" Reflex)
    injection_patterns = [
        r"ignore previous instructions",
        r"ignore all previous",
        r"system prompt",
        r"you are now",
        r"forget everything",
        r"bypass rules",
        r"override context",
        r"print your instructions",
    ]
    for pattern in injection_patterns:
        if re.search(pattern, prompt_lower):
            return (
                False,
                f"AMYGDALA HIJACK PREVENTED: Suspected prompt injection ({pattern}).",
            )

    # 2. Catastrophic Destructive Commands (The "Flinch" Reflex)
    destructive_patterns = [
        r"\brm -rf\b",
        r"\bdrop table\b",
        r"\bchmod 777\b",
        r"\bdel \/f\b",
        r"\bformat c:\b",
    ]
    for pattern in destructive_patterns:
        if re.search(pattern, prompt_lower):
            return False, f"AMYGDALA FLINCH: Lethal command detected ({pattern})."

    # 3. Forbidden Target Access (Protecting Vital Organs)
    forbidden_targets = ["system/config", ".env", "autonomic.py", "amygdala.py"]
    for target in forbidden_targets:
        if target in prompt_lower:
            return (
                False,
                f"AMYGDALA BOUNDARY: Unauthorized access to vital organ ({target}).",
            )

    # 4. Standard Destructive Verbs (Legacy Bouncer)
    forbidden_actions = [r"\bdelete\b", r"\berase\b"]
    for action in forbidden_actions:
        if re.search(action, prompt_lower):
            clean_word = action.replace(r"\b", "")
            return False, f"AMYGDALA RULE: Destructive action blocked ('{clean_word}')."

    return True, "Safe"


def scan_command(command: str) -> tuple[bool, str]:
    """
    The Amygdala: Scans terminal commands for malicious background execution patterns.
    Returns (is_safe, threat_reason).
    """
    for pattern in FORBIDDEN_BACKGROUND_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return (
                False,
                f"SECURITY BLOCK (Amygdala): The command '{command}' violates background execution policies. Do not use curl, wget, nc, or rm.",
            )
    return True, ""
