import logging
from models import generate

log = logging.getLogger('medcare.models')
MODEL_CATALOG = {
    'airavata': {'label': 'Airavata', 'kind': 'text-generation', 'model_id': 'ai4bharat/Airavata', 'note': '7B Hindi instruction model; Hugging Face access may require accepting its terms.'},
    'qwen': {'label': 'Qwen', 'kind': 'text-generation', 'model_id': 'Qwen/Qwen2.5-1.5B-Instruct', 'note': '1.5B multilingual instruct model; easier to run locally.'},
    'sarvam': {'label': 'Sarvam AI', 'kind': 'text-generation', 'model_id': 'sarvam-105b', 'note': 'Cloud LLM via Sarvam API. Requires SARVAM_API_KEY.'},
    'vakyansh': {'label': 'Vakyansh', 'kind': 'automatic-speech-recognition', 'model_id': 'Harveenchadha/vakyansh-wav2vec2-hindi-him-4200', 'note': 'Hindi ASR model, not a text chat generator. Voice tab integration is next.'},
    'local': {'label': 'Deterministic fallback', 'kind': 'fallback', 'model_id': None, 'note': 'Safe local wording fallback when a model is unavailable.'},
}


def catalog(): return MODEL_CATALOG


def safe_model_response(model_key: str, user_message: str, draft: str) -> tuple[str, dict]:
    """Let a selected text model phrase a backend-controlled answer.

    The draft contains the only approved facts. Models cannot change state,
    triage, fields, or medical rules; an unavailable/invalid model falls back.
    """
    if model_key not in MODEL_CATALOG or model_key == 'local':
        return draft, {'model_key': 'local', 'model_label': MODEL_CATALOG['local']['label'], 'model_status': 'fallback'}
    if MODEL_CATALOG[model_key]['kind'] != 'text-generation':
        return draft, {'model_key': model_key, 'model_label': MODEL_CATALOG[model_key]['label'], 'model_status': 'not_text_generator', 'model_note': MODEL_CATALOG[model_key]['note']}
    prompt = f'''You are the {MODEL_CATALOG[model_key]['label']} wording layer for Hinglish MedCare.
Rewrite the approved backend response below in short, empathetic, simple Indian Hinglish/Hindi or clear English matching the user's language.
STRICT RULES: output only the rewritten response; do not add, remove, or change medical facts; do not change urgency; do not diagnose; do not invent symptoms, remedies, patient details, or questions; preserve any WHAT TO DO NOW, WHAT TO AVOID, WHEN TO SEEK MEDICAL HELP, FOLLOW-UP, and Source headings.
User message: {user_message}
Approved backend response:
{draft}
'''
    try:
        raw = generate(model_key, prompt).strip()
        if raw and len(raw) <= 6000:
            return raw, {'model_key': model_key, 'model_label': MODEL_CATALOG[model_key]['label'], 'model_status': 'generated'}
        return draft, {'model_key': model_key, 'model_label': MODEL_CATALOG[model_key]['label'], 'model_status': 'invalid_output_fallback'}
    except Exception as exc:
        log.warning('model unavailable key=%s error=%s', model_key, exc)
        return draft, {'model_key': model_key, 'model_label': MODEL_CATALOG[model_key]['label'], 'model_status': 'unavailable_fallback', 'model_error': str(exc)[:240]}
