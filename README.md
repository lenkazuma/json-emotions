# json-emotions

AI chat with Lottie (JSON) animations. Ask "Mrs Fox" a question and she answers, then plays the animation that matches the tone of her reply — an introduction, a question, praise for a correct answer, encouragement after a wrong one, or a congratulation.

A second demo turns free-form robot arm instructions (Chinese or English) into one of a fixed set of actions.

## Apps

| Script | What it does |
| --- | --- |
| `app_emotions.py` | Tutor chat. Each answer is followed by a Lottie animation picked by the model, with 👍/👎 feedback per reply. |
| `action_select.py` | Maps instructions such as "请你挥挥手" or "Can you jump?" to `wave` / `nod` / `rotate` / `jump` / `blink`, or reports that none applies. |

Both use OpenAI tool calling with an `enum` of allowed ids, so the model can only choose animations or actions that actually exist. Anything else is ignored rather than being turned into a file path.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app_emotions.py      # or: streamlit run action_select.py
```

Enter your OpenAI API key in the sidebar. To avoid typing it each time, copy `.env.example` to `.env` and set `OPENAI_API_KEY`; `.env` is git-ignored. The default model is `gpt-4o-mini` and can be changed in the sidebar.

## Animations

The Lottie files in [`animation/`](animation) follow the brief in `animation/Job Brief - Fox Animation - 23 Jan 2021.pdf`:

| Id | Length | Line |
| --- | --- | --- |
| `characterIntro` | 7s | "Hello, I am Mrs Fox, I am from Australia, I will be your tutor" |
| `Asking` | 3s | "Which one is …?" |
| `correct1` / `correct2` | 3s | "You are correct!" / "Great job" |
| `wrong1` / `wrong2` | 3s | "Try again, you can do it" / "Let's try again" |
| `congratulation` | 5s | "Wonderful, you have completed the chapter" |

To add one, drop the JSON into `animation/` and add its id and a short description to `ANIMATIONS` in [`chat_core.py`](chat_core.py).

## Tests

```bash
pip install pytest
pytest -q
```

The tests use a fake OpenAI client and Streamlit's `AppTest`, so no API key or network is needed.

## License

MIT
