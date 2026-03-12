import json
import logging
from typing import Optional, Dict, Any

from groq import Groq

from app.utils.settings import get_settings

logger = logging.getLogger(__name__)


def generate_study_plan(
    ability: float,
    accuracy: float,
    weak_topics: list[str],
    max_difficulty: float,
) -> Optional[Dict[str, Any]]:
    """
    Call the Groq LLM to generate a structured 3-step learning plan.

    Returns a dict with keys step_1, step_2, step_3 or None if the
    LLM is unavailable or an error occurs. Errors are logged but not fatal.
    """
    settings = get_settings()
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY is not set; skipping study plan generation.")
        return None

    weak_topics_str = ", ".join(weak_topics) if weak_topics else "None"

    system_prompt = (
        "You are an expert GRE tutor generating concise, practical study plans.\n"
        "Respond ONLY with a compact JSON object with three fields: "
        '\"step_1\", \"step_2\", and \"step_3\". Do not include any extra text.'
    )

    user_prompt = (
        "A student completed an adaptive diagnostic test.\n\n"
        f"Final Ability Score: {ability:.3f}\n"
        f"Accuracy: {accuracy * 100:.1f}%\n"
        f"Topics with most mistakes: {weak_topics_str}\n"
        f"Highest Difficulty Reached: {max_difficulty:.3f}\n\n"
        "Generate a clear 3-step personalized learning plan focused on GRE-style preparation. "
        "Each step should be concrete and actionable, mentioning specific practice types, "
        "time allocation, and how to review mistakes."
    )

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content  # type: ignore[assignment]
        plan = json.loads(content)
        if not all(key in plan for key in ("step_1", "step_2", "step_3")):
            raise ValueError("LLM response missing required keys")
        return {
            "step_1": str(plan["step_1"]),
            "step_2": str(plan["step_2"]),
            "step_3": str(plan["step_3"]),
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to generate study plan via Groq LLM: %s", exc)
        return None

