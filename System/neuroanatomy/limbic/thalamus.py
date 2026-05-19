from System.core.paths import ROOT_DIR
import yaml  # type: ignore
from litellm import completion  # type: ignore
from rich.console import Console
from System.neuroanatomy.systemic.immune_system import vault

console = Console()

CONFIG_PATH = ROOT_DIR / "System" / "config" / "agents.yaml"


def filter_attention(prompt: str, raw_memory: str) -> str:
    """
    The Thalamus (Semantic Attention Filter).
    Reads the Neocortex memory and extracts ONLY the tokens relevant to the current task.
    """
    # 1. Biological Fast-Path: If the memory is small, don't waste time filtering it.
    if len(raw_memory) < 2000:
        return raw_memory

    console.print(
        "[dim magenta]🧠 Thalamus Active: Filtering context noise...[/dim magenta]"
    )

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Use the cheapest possible model for the subconscious filter
        model = config.get("models", {}).get("gpt_mini", "gpt-4o-mini")

        # ⚡ THE FIX: Use the secure vault to check for keys!
        if vault.get_api_key_for_model(
            "anthropic/claude-3-haiku"
        ) and not vault.get_api_key_for_model("openai/gpt-4o-mini"):
            model = config.get("models", {}).get(
                "claude_haiku", "claude-3-haiku-20240307"
            )
    except Exception:
        model = "gpt-4o-mini"

    system_prompt = """You are the Thalamus of Brain OS.
Your job is to filter the long-term memory (Neocortex) and extract ONLY the exact bullet points, facts, and context highly relevant to the User's current task.
Do NOT rewrite the memory. Do NOT answer the prompt.
Just output the exact lines from the memory that are relevant.
If absolutely nothing in the memory is relevant to the task, output "No relevant context found."
Keep it as dense and short as possible."""

    try:
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"USER TASK:\n{prompt}\n\nRAW MEMORY:\n{raw_memory}",
                },
            ],
            temperature=0.0,
        )
        filtered_memory = str(response.choices[0].message.content).strip()
        return f"--- FILTERED CONTEXT (THALAMUS) ---\n{filtered_memory}"

    except Exception as e:
        console.print(f"[dim red]Thalamus API Error. Bypassing filter. ({e})[/dim red]")
        # Structural fallback: just grab the most recent 4000 characters
        return raw_memory[-4000:]


def process_sensory_input(source: str, payload: str) -> str:
    """
    The Thalamic gateway for ascending sensory data from the Spine.
    Filters, prioritizes, and formats impulses before they reach the Prefrontal Cortex.
    """
    return f"<ascending_stimulus source='{source}'>\n{payload}\n</ascending_stimulus>"


def route_public_pulse(sender_id: str, payload: str, signature: str) -> str:
    """
    Sensory gating for external network traffic.
    Instantly routes PUBLIC domain traffic to the Exocortex, keeping it isolated
    from internal Prefrontal Cortex planning loops.
    """
    from rich.console import Console

    Console().print(
        "[bold magenta]👁️ Thalamus: Routing external stimulus to Exocortex...[/bold magenta]"
    )

    from System.neuroanatomy.cortical.exocortex import Exocortex

    exo = Exocortex()
    return exo.process_inbound_pulse(sender_id, payload, signature)


async def route_sensory_input(prompt: str) -> tuple[bool, str, str, str, dict]:
    """
    THALAMUS: The Sensory Switchboard.
    Analyzes an autonomous prompt using the Dispatcher to determine validity, routing, and domain.
    """
    import asyncio
    from rich.console import Console
    from System.neuroanatomy.systemic.enteric import get_gut_reaction, save_gut_reaction
    from System.neuroanatomy.limbic.amygdala import scan_prompt
    from System.core.dna import get_dna_config
    from System.llm import acompletion, get_system_context
    from System.neuroanatomy.systemic.immune_system import vault
    from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere
    from System.core.schemas import DispatcherResult
    from System.neuroanatomy.autonomic.interoception import log_metabolism

    console = Console()

    # --- 🦠 ENTERIC NERVOUS SYSTEM (Gut Reaction) ---
    gut_reflex = await asyncio.to_thread(get_gut_reaction, prompt)
    if gut_reflex:
        return gut_reflex
    zero_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # --- 🚨 THE AMYGDALA (Threat Detection) ---
    is_safe, threat_reason = await asyncio.to_thread(scan_prompt, prompt)
    if not is_safe:
        return False, threat_reason, "NONE", "NONE", zero_usage

    # --- 🧠 PREFRONTAL DISPATCHER (LLM Routing) ---
    dispatcher_cfg = get_dna_config()["agents"]["dispatcher"]
    system_prompt = dispatcher_cfg["system_prompt"] + get_system_context(
        ["Meta"], prompt=prompt
    )

    try:
        base_model = get_dna_config()["models"][dispatcher_cfg["model"]]
        actual_model = route_hemisphere("DISPATCHER", base_model)

        response = await acompletion(
            model=actual_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            api_key=vault.get_api_key_for_model(actual_model),
        )
        raw_text = str(response.choices[0].message.content).strip()

        usage_data = zero_usage.copy()
        if hasattr(response, "usage") and response.usage:
            usage_data["prompt_tokens"] = int(
                getattr(response.usage, "prompt_tokens", 0)
            )
            usage_data["completion_tokens"] = int(
                getattr(response.usage, "completion_tokens", 0)
            )
            usage_data["total_tokens"] = int(getattr(response.usage, "total_tokens", 0))

        if "REJECTED:" in raw_text.upper():
            reason = raw_text.upper().split("REJECTED:")[1].strip(" \"'}\n").strip()
            return False, reason, "NONE", "NONE", usage_data

        try:
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:-3]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:-3]

            data = DispatcherResult.model_validate_json(clean_text.strip())
            route = data.route.strip().upper()
            domain = data.domain.strip().upper()

            console.print(
                f"[dim green]🧠 Thalamus Reasoning: {data.reasoning}[/dim green]"
            )

        except Exception as e:
            route = "UNKNOWN"
            domain = "NONE"
            console.print(f"[dim red]Thalamus Parsing Error: {e}[/dim red]")

        # --- THE VAGUS NERVE: Log metabolism & save memory ---
        await asyncio.to_thread(log_metabolism, usage_data.get("total_tokens", 0))
        await asyncio.to_thread(
            save_gut_reaction, prompt, True, "Approved.", route, domain
        )

        return True, "Approved.", route, domain, usage_data

    except Exception as e:
        return False, f"Dispatcher API Error: {str(e)}", "NONE", "NONE", zero_usage
