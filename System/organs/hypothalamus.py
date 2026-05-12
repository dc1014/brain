import asyncio
from typing import Callable, Any
from rich.console import Console

console = Console()


async def regulate_api_heartbeat(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    The Hypothalamus (Homeostasis & Exponential Backoff).
    Intercepts API 429 (Rate Limit) errors and forces the Swarm to 'breathe'
    and slow down before attempting to hit the cloud again.
    """
    max_retries = 5
    base_delay = 2.0

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Detect Rate Limits, Too Many Requests, or Quota Exhaustion
            if (
                "429" in error_str
                or "rate limit" in error_str
                or "too many requests" in error_str
            ):
                if attempt == max_retries - 1:
                    raise Exception(
                        "HYPOTHALAMUS FAILURE: Max retries exhausted. System cardiac arrest."
                    ) from e

                # Exponential backoff: 2s, 4s, 8s, 16s
                sleep_time = base_delay * (2**attempt)
                console.print(
                    "\n[bold red]🫀 Hypothalamus Alert: System Overheating (API Rate Limit).[/bold red]"
                )
                console.print(
                    f"[dim yellow]Inducing biological backoff. Resting for {sleep_time} seconds (Attempt {attempt + 1}/{max_retries})...[/dim yellow]"
                )
                await asyncio.sleep(sleep_time)
            else:
                # If it's a 500 error or auth error, don't retry. Fail instantly.
                raise e
