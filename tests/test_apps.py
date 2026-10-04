from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def no_env_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")


@pytest.mark.parametrize("script", ["app_emotions.py", "action_select.py"])
def test_app_renders_and_requires_key(script):
    at = AppTest.from_file(str(ROOT / script), default_timeout=30).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert any("API key" in w.value for w in at.warning)


def test_history_replays_animation_and_feedback():
    at = AppTest.from_file(str(ROOT / "app_emotions.py"), default_timeout=30)
    at.session_state["history"] = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "Hello!", "animation": "characterIntro"},
        {"role": "assistant", "content": "No animation", "animation": None},
    ]
    at.run()
    assert not at.exception
    assert [m.markdown[0].value for m in at.chat_message] == ["hi", "Hello!", "No animation"]
