# --- System/neuroanatomy/limbic/thalamus.py ---
import asyncio
from rich.console import Console
from pydantic import BaseModel, Field
from litellm import completion  # type: ignore

from System.core.dna import get_dna_config
from System.neuroanatomy.systemic.immune_system import vault
from System.neuroanatomy.autonomic.interoception import log_metabolism
from System.neuroanatomy.limbic.amygdala import scan_prompt

console = Console()


class DispatcherResult(BaseModel):
    reasoning: str = Field(description="Step by step logic for routing.")
    route: str = Field(description="The assigned route.")
    domain: str = Field(description="The assigned domain.")


def filter_attention(prompt: str, raw_memory: str) -> str:
    # 1. Biological Fast-Path: If the memory is small, don't waste time filtering it.
    if len(raw_memory) < 2000:
        return raw_memory

    console.print(
        "[dim magenta][*] Thalamus Active: Filtering context noise...[/dim magenta]"
    )

    # Active Synchronous Token Pruning
    try:
        config = get_dna_config()
        model = config.get("models", {}).get("fast", "openai/gpt-4o-mini")

        routed_model, api_key = vault.resolve_routing(model)
        gateway_url = vault.get_secret("GATEWAY_BASE_URL")
        if gateway_url:
            api_key = vault.get_secret("GATEWAY_API_KEY") or api_key

        kwargs = {
            "model": routed_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are the Thalamus. Extract and summarize ONLY the information from the provided memory that is strictly relevant to answering the user's prompt. Discard all other noise to save tokens.",
                },
                {
                    "role": "user",
                    "content": f"USER PROMPT: {prompt}\n\nRAW MEMORY:\n{vault.mask_secrets(raw_memory)}",
                },
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
            "api_key": api_key,
        }
        if gateway_url:
            kwargs["api_base"] = gateway_url

        response = completion(**kwargs)
        filtered_text = response.choices[0].message.content

        if hasattr(response, "usage") and response.usage:
            total_tokens = getattr(response.usage, "total_tokens", 0)
            log_metabolism(total_tokens)

        return filtered_text.strip() if filtered_text else raw_memory

    except Exception as e:
        console.print(
            f"[dim red]Thalamus filtering degraded (Bypassing): {e}[/dim red]"
        )
        return raw_memory


async def route_sensory_input(prompt: str) -> tuple[bool, str, str, str, dict]:
    """Evaluates incoming stimuli, checks reflexes, and assigns an execution route."""
    from System.llm import run_agent_async, clean_json_output

    usage_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    try:
        from System.neuroanatomy.systemic.enteric import get_gut_reaction

        gut_reaction = get_gut_reaction(prompt)
        if gut_reaction:
            return gut_reaction
    except Exception:
        pass

    is_safe, block_reason = scan_prompt(prompt)
    if not is_safe:
        return False, block_reason, "NONE", "NONE", usage_data

    # ⚡ THE FIX: Secure dynamic lookup of the Thalamus name to ensure the config maps properly
    dna = get_dna_config()
    dispatcher_name = (
        dna.get("agents", {}).get("dispatcher", {}).get("name", "Thalamus (Dispatcher)")
    )

    # ⚡ SAFETY NET: Hardcoded fallback prompt if ALL config files are mysteriously missing
    FALLBACK_PROMPT = """You are the Thalamus (Dispatcher).
Your job is to analyze the user's prompt and route it to the correct subsystem.
Output valid JSON matching this schema:
{
    "reasoning": "Step-by-step logic",
    "route": "FAST, WORKSPACE, CODE_FRONTEND, CODE_BACKEND, CODE_FULLSTACK, etc.",
    "domain": "GENERAL, STUDIO, PERSONAL, etc."
}
If the user is just asking a question, making a joke, or chatting, route to FAST.
"""

    try:
        response = await run_agent_async(
            role_name=dispatcher_name,
            system_prompt=FALLBACK_PROMPT,
            user_prompt=f"<external_stimulus>\n{prompt}\n</external_stimulus>",
            model_string="gemini/gemini-2.5-flash",
            route="FAST",
            domain="META",
        )

        usage_data = response.usage
        raw_text = response.text

        if "REJECTED:" in raw_text.upper():
            reason = raw_text.upper().split("REJECTED:")[1].strip(" \"'\n").strip()
            return False, reason, "NONE", "NONE", usage_data

        try:
            clean_text = clean_json_output(raw_text)

            data = DispatcherResult.model_validate_json(clean_text)
            route = data.route.strip().upper()
            domain = data.domain.strip().upper()

            console.print(
                f"[dim green][*] Thalamus Reasoning: {data.reasoning}[/dim green]"
            )
            await asyncio.to_thread(log_metabolism, usage_data.get("total_tokens", 0))

            return True, data.reasoning, route, domain, usage_data

        except Exception as e:
            console.print(f"[dim red]Thalamus Parsing Error: {e}[/dim red]")
            return (
                True,
                "Fallback routing engaged due to parsing error.",
                "UNKNOWN",
                "NONE",
                usage_data,
            )

    except Exception as e:
        console.print(f"[dim red]Thalamus Routing Crash: {e}[/dim red]")
        return (
            True,
            "Fallback routing engaged due to API error.",
            "UNKNOWN",
            "NONE",
            usage_data,
        )


def process_sensory_input(source: str, prompt: str) -> None:
    from System.core.orchestrator import dispatch_task

    asyncio.run(dispatch_task(prompt, origin=source))


def route_public_pulse(sender_id: str, payload: str, signature: str) -> str:
    from System.core.orchestrator import dispatch_task

    asyncio.run(dispatch_task(payload, origin=f"public:{sender_id}"))
    return "Pulse received and queued."
