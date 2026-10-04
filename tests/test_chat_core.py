import json
from types import SimpleNamespace

import pytest

import chat_core
from chat_core import ANIMATIONS, NO_ACTION, ask, choose_action, choose_animation, load_animation


class FakeClient:
    """Mimics client.chat.completions.create and records the calls."""

    def __init__(self, *, content="", tool_args=None, tool_name=None):
        self.calls = []
        self._content = content
        self._tool_args = tool_args
        self._tool_name = tool_name
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        tool_calls = None
        if self._tool_args is not None:
            name = self._tool_name or kwargs["tool_choice"]["function"]["name"]
            args = self._tool_args if isinstance(self._tool_args, str) else json.dumps(self._tool_args)
            tool_calls = [SimpleNamespace(function=SimpleNamespace(name=name, arguments=args))]
        message = SimpleNamespace(content=self._content, tool_calls=tool_calls)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.mark.parametrize("animation_id", sorted(ANIMATIONS))
def test_every_animation_loads(animation_id):
    data = load_animation(animation_id)
    assert isinstance(data, dict) and "layers" in data


@pytest.mark.parametrize("bad", ["../requirements", "missing", "", "Asking.json", "..\\app_emotions"])
def test_unknown_animation_ids_rejected(bad):
    assert load_animation(bad) is None


def test_ask_includes_history_and_system_prompt():
    client = FakeClient(content="是的")
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello", "animation": "Asking"}]
    assert ask(client, history, "1+1=2?", "m") == "是的"
    messages = client.calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert [m["content"] for m in messages[1:]] == ["hi", "hello", "1+1=2?"]
    assert all(set(m) == {"role", "content"} for m in messages)


def test_choose_animation_forces_tool_with_enum():
    client = FakeClient(tool_args={"animation_id": "wrong1"})
    assert choose_animation(client, "1+1=3?", "不对哦", "m") == "wrong1"
    call = client.calls[0]
    assert call["tool_choice"]["function"]["name"] == "show_animation"
    enum = call["tools"][0]["function"]["parameters"]["properties"]["animation_id"]["enum"]
    assert set(enum) == set(ANIMATIONS)


@pytest.mark.parametrize("args", [{"animation_id": "../../etc/passwd"}, {}, "not json"])
def test_choose_animation_rejects_bad_output(args):
    assert choose_animation(FakeClient(tool_args=args), "q", "a") is None


def test_choose_animation_without_tool_call():
    assert choose_animation(FakeClient(content="hmm"), "q", "a") is None


def test_choose_action():
    assert choose_action(FakeClient(tool_args={"action": "wave"}), "请你挥挥手") == "wave"
    assert choose_action(FakeClient(tool_args={"action": "dance"}), "dance") == NO_ACTION
    assert choose_action(FakeClient(tool_args={"action": "wave"}, tool_name="other"), "x") == NO_ACTION


def test_action_enum_includes_none():
    client = FakeClient(tool_args={"action": NO_ACTION})
    assert choose_action(client, "你能讲话不") == NO_ACTION
    enum = client.calls[0]["tools"][0]["function"]["parameters"]["properties"]["action"]["enum"]
    assert set(enum) == set(chat_core.ACTIONS) | {NO_ACTION}
