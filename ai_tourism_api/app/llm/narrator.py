"""
LAYER 4 — LARGE LANGUAGE MODEL (Narrator)
==========================================
Rewrites verified landmark facts (from the Knowledge Database) into a
natural, story-style narrative. Never invents facts — the system prompt
constrains the model to only the facts it is given.

Provider-agnostic: set LLM_PROVIDER=openai|gemini|none in the environment.
"none" (the default) returns a clean template-based narrative with zero
external calls, so the API works out of the box without any API key.
"""
from app.config import settings

SYSTEM_PROMPT = (
    "You are a professional tour guide narrator. Rewrite the given verified "
    "facts about a landmark into an engaging, story-style narration of "
    "roughly 120-200 words, in the requested language. Do NOT invent any "
    "fact that is not present in the input. If information is missing, "
    "gracefully omit it rather than making something up."
)


def _template_fallback(facts: dict, language: str) -> str:
    name = facts.get("name", "This landmark")
    history = facts.get("history") or "has a rich and storied past."
    era = facts.get("era")
    fun_facts = facts.get("fun_facts") or []

    parts = [f"{name}."]
    if era:
        parts.append(f"Dating back to the {era},")
    parts.append(history)
    if fun_facts:
        parts.append("Here's something you might not know: " + fun_facts[0])
    return " ".join(parts)


def _call_openai(facts: dict, language: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    user_prompt = (
        f"Target language: {language}\n"
        f"Verified facts (JSON): {facts}\n"
        "Write the narration now."
    )
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""


def _call_gemini(facts: dict, language: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        settings.LLM_MODEL or "gemini-1.5-pro", system_instruction=SYSTEM_PROMPT
    )
    user_prompt = f"Target language: {language}\nVerified facts (JSON): {facts}\nWrite the narration now."
    response = model.generate_content(user_prompt)
    text = response.text
    return text.strip() if text else ""


def generate_story(facts: dict, language: str = "en") -> str:
    provider = settings.LLM_PROVIDER.lower()
    try:
        if provider == "openai" and settings.OPENAI_API_KEY:
            return _call_openai(facts, language)
        if provider == "gemini" and settings.GEMINI_API_KEY:
            return _call_gemini(facts, language)
    except Exception as exc:  # never let a story-writing failure break the pipeline
        return _template_fallback(facts, language) + f" (note: narration service unavailable: {exc})"

    return _template_fallback(facts, language)
