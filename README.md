# Hinglish MedCare

A local, text-first rural-health assistance prototype for **burns and scalds**. It combines a browser chat interface, explicit workflow state, structured SQLite records, deterministic safety/triage rules, and selectable language-model wording layers.

> **Healthcare safety:** This is an informational development prototype, not a doctor or diagnostic tool. The bundled `guidelines/burns_scalds.json` is explicitly a draft. Verify every field, rule, and guidance statement against the official guideline selected by the project team before any real-world deployment. Do not use it to replace emergency care.

## Model comparison tabs

The web UI has three independent subtabs. Each tab stores its own conversation/case so you can send the same messages to each model and compare the responses:

- **Airavata** — `ai4bharat/Airavata`, a 7B Hindi instruction-tuned text-generation model. Its Hugging Face access terms may need to be accepted manually before download.
- **Qwen** — `Qwen/Qwen2.5-1.5B-Instruct`, a smaller multilingual text-generation model and the practical first model to try locally.
- **Vakyansh** — `Harveenchadha/vakyansh-wav2vec2-hindi-him-4200`, a Hindi automatic speech-recognition model. It converts audio to text; it is **not a text chat generator**. Its tab is included for comparison and currently uses the safe fallback for typed messages. It can be connected to the future voice pipeline without pretending it generates chat answers.

The backend continues to own extraction, state transitions, emergency overrides, severity, guidance facts, persistence, and follow-up. Airavata/Qwen only rewrite the approved backend response into natural Hinglish/Hindi/English. If a model is unavailable, the tab reports `unavailable_fallback` and uses safe deterministic wording.

The model layer is lazy: a model is downloaded only when its tab is used. Local weights can require significant disk/RAM/VRAM, especially Airavata.

## Current scope

Implemented: incident-first burn intake, immediate WHO-grounded first-aid response for serious cases, patient creation after the incident is assessed, returning-patient lookup, persistent calls/messages/assessments/follow-ups, Hinglish/Roman Hindi/English text extraction, one-question-at-a-time workflow, deterministic emergency override, configurable triage rules, model comparison tabs, grounded prototype guidance, final summary, responsive UI, and tests.

Not implemented: voice, telephony, WhatsApp, PHC/ambulance integration, reminders, other medical conditions, or clinical validation.

## Run locally

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python init_db.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. The app starts with a safe local fallback and does not download a model until you send a message in a model tab. The first Airavata/Qwen request can take a long time while Hugging Face downloads the weights.

If Hugging Face asks for access to Airavata, open the model page, accept the model terms, and make sure your local Hugging Face account/token is configured. Airavata is a 7B model and may be difficult to run on a laptop without sufficient memory. Qwen2.5-1.5B is the lighter first choice.

## Environment

`DATABASE_URL` defaults to `sqlite:///./medcare.db`; `MODEL_PROVIDER=local`; `SARVAM_API_KEY` is only needed for the preserved Sarvam evaluation path. Never commit `.env` or credentials.

## Architecture

- `app/main.py`: FastAPI page, model catalog, and REST endpoints.
- `app/db/`: SQLAlchemy engine and ORM models for patients, calls, messages, assessments, and follow-ups.
- `app/services/extraction_service.py`: explicit, conservative local Hinglish extraction and emergency keyword layer.
- `app/services/triage_service.py`: missing-field priority, deterministic RED/YELLOW/GREEN/UNKNOWN rules, WHO-grounded guidance and follow-up.
- `app/services/model_service.py`: safe model adapter; selected text models can only phrase an approved backend draft.
- `models.py`: lazy Hugging Face model abstraction for Airavata, Qwen, and the preserved Airavata/OpenHathi/Sarvam evaluation providers.
- `app/templates/` and `app/static/`: vanilla HTML/CSS/JavaScript UI with three independent model tabs. No medical/business rules live in JavaScript.
- `guidelines/burns_scalds.json`: shared draft checklist.

## Model API behavior

`GET /api/models` lists the available model IDs and task type. `POST /api/calls/{call_uid}/message` accepts `model_key` values `airavata`, `qwen`, `vakyansh`, or `local`. The response includes a `model` object with `model_status`, such as `generated`, `unavailable_fallback`, or `not_text_generator`.

## Example conversation

The chat starts without asking for identity details. Describe the incident first. The system gives immediate first-aid/safety guidance, checks for emergency indicators, and asks one burn question at a time. After the incident assessment and guidance, it asks for the patient name and age, saves the final summary, and creates a follow-up record so the user can return with updates.

```text
garam paani se haath jal gaya
abhi hua
smoke nahi tha
hatheli se chhota
sirf laal hai
mild pain hai
nahi around
Shashank
20
```

The assistant asks exactly one next question at each incomplete turn. It does not infer age, size, pain, or smoke exposure from the first message. The first-aid wording is based on the [WHO Burns fact sheet](https://www.who.int/news-room/fact-sheets/detail/burns), accessed during this implementation update; it is not a substitute for emergency or clinical care.

## Tests

```bash
python -m pytest -q
```

The test suite covers extraction, no-hallucination defaults, corrections, one-question priority, emergency flags, triage, persistence, and API flow. Heavy model weights are not downloaded during tests; model tabs fall back cleanly when `torch`/`transformers` or model files are unavailable.

The original evaluation framework remains intact:

```bash
python run_eval.py --condition burns_scalds --models sarvam
```

That command may require an API key or downloaded model depending on provider. The new app does not depend on it.

## Future extension

Voice can connect Vakyansh ASR to `input_type`, `transcript`, `audio_path`, and `confidence`, then feed the transcript into the same deterministic conversation pipeline. A condition registry can add guideline, fields, priority, extraction prompt, triage, and guidance per condition. No voice or PHC integration is faked in this release.
