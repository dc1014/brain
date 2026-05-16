import os


def route_hemisphere(route: str, cloud_model: str) -> str:
    """
    The Corpus Callosum (Hemispheric Bridging).
    Routes tasks to the Left Hemisphere (Local SLM) or Right Hemisphere (Cloud LLM).
    """
    # ⚡ STRICT CONFIG COMPLIANCE: If the host disables local models, stay in the Cloud
    use_local = os.environ.get("USE_LOCAL_SLM", "false").lower() == "true"
    local_model = os.environ.get("LOCAL_MODEL_NAME", "ollama/llama3")

    if not use_local:
        return cloud_model

    # LEFT BRAIN: Fast, analytical, high-privacy, zero-cost.
    LEFT_BRAIN_ROUTES = {
        "DISPATCHER",
        "WORKSPACE",
        "READ_ONLY",
        "FAST",
        "AMYGDALA",
        "MEMORY",
        "JOURNAL",
        "SENSE",
        "SUBCONSCIOUS_DAYDREAM",  # DMN background maintenance
        "SUBCONSCIOUS_FORAGE",  # Background scraping/foraging
        "WERNICKE",  # Semantic filtering
    }

    if route.upper() in LEFT_BRAIN_ROUTES:
        return local_model

    # RIGHT BRAIN: Creative, abstract, expensive (FORGE, SWARM)
    return cloud_model
