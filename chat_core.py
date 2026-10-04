"""Model calls and asset lookup shared by the Streamlit apps (no Streamlit imports here)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ANIMATION_DIR = Path(__file__).parent / "animation"
DEFAULT_MODEL = "gpt-4o-mini"

ANIMATIONS: Dict[str, str] = {
    "Asking": "3s - asks the learner a question: 'Which one is ...?'",
    "characterIntro": "7s - introduces the tutor: 'Hello, I am Mrs Fox, I am from Australia, I will be your tutor'",
    "congratulation": "5s - celebrates finishing: 'Wonderful, you have completed the chapter'",
    "correct1": "3s - confirms a right answer: 'You are correct!'",
    "correct2": "3s - praises: 'Great job'",
    "wrong1": "3s - encourages after a mistake: 'Try again, you can do it'",
    "wrong2": "3s - gently corrects: 'Let's try again'",
}

ACTIONS: Dict[str, str] = {
    "wave": "wave a hand",
    "nod": "nod the head",
    "rotate": "turn around",
    "jump": "jump",
    "blink": "blink the eyes",
}
NO_ACTION = "none"

SYSTEM_PROMPT = (
    "You are Mrs Fox, a warm and encouraging tutor. Answer clearly and kindly in the "
    "language the user writes in. When the user makes a claim, say whether it is correct."
)


def load_animation(animation_id: str) -> Optional[Dict[str, Any]]:
    """Return the Lottie JSON for a known animation id, or None for anything else."""
    if animation_id not in ANIMATIONS:
        return None
    path = ANIMATION_DIR / f"{animation_id}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _choice_tool(name: str, description: str, field: str, options: Dict[str, str]) -> Dict[str, Any]:
    listing = "; ".join(f"{key}: {desc}" for key, desc in options.items())
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    field: {"type": "string", "enum": list(options), "description": listing},
                },
                "required": [field],
                "additionalProperties": False,
            },
        },
    }


def _forced_choice(client: Any, model: str, prompt: str, tool: Dict[str, Any], field: str) -> Optional[str]:
    name = tool["function"]["name"]
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        tools=[tool],
        tool_choice={"type": "function", "function": {"name": name}},
    )
    calls = response.choices[0].message.tool_calls or []
    for call in calls:
        if call.function.name != name:
            continue
        try:
            value = json.loads(call.function.arguments or "{}").get(field)
        except ValueError:
            return None
        allowed = tool["function"]["parameters"]["properties"][field]["enum"]
        return value if value in allowed else None
    return None


def ask(client: Any, history: List[Dict[str, str]], question: str, model: str = DEFAULT_MODEL) -> str:
    """Answer `question`, giving the model the previous turns for context."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(model=model, temperature=0.3, messages=messages)
    return response.choices[0].message.content or ""


def choose_animation(client: Any, question: str, answer: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    """Pick the animation that best matches the tutor's reply; None if the model returns nothing usable."""
    tool = _choice_tool(
        "show_animation",
        "Show the tutor animation that best matches the reply.",
        "animation_id",
        ANIMATIONS,
    )
    prompt = (
        "Pick the animation that best fits the tutor's reply. Use correct*/wrong* when the reply "
        "judges the user's claim, congratulation for praise or milestones, characterIntro when "
        "the tutor introduces herself, otherwise Asking.\n\n"
        f"User: {question}\nTutor: {answer}"
    )
    return _forced_choice(client, model, prompt, tool, "animation_id")


def choose_action(client: Any, instruction: str, model: str = DEFAULT_MODEL) -> str:
    """Map a free-form instruction (any language) to one robot action id or NO_ACTION."""
    options = {**ACTIONS, NO_ACTION: "the instruction asks for none of these actions"}
    tool = _choice_tool("perform_action", "Perform one robot arm action.", "action", options)
    prompt = f"Which action does this instruction ask for?\n\nInstruction: {instruction}"
    return _forced_choice(client, model, prompt, tool, "action") or NO_ACTION
