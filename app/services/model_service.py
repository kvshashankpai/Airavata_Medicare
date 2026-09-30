import logging
from models import generate

log = logging.getLogger('medcare.models')

MODEL_CATALOG = {
    'airavata': {
        'label': 'Airavata',
        'kind': 'text-generation',
        'model_id': 'ai4bharat/Airavata',
        'note': '7B Hindi instruction model used only for final user-facing wording after backend safety/triage.'
    },
    'qwen': {
        'label': 'Qwen',
        'kind': 'text-generation',
        'model_id': 'Qwen/Qwen2.5-1.5B-Instruct',
        'note': 'Available for comparison in the legacy evaluation path; the active chatbot uses Airavata only.'
    },
    'sarvam': {
        'label': 'Sarvam AI',
        'kind': 'text-generation',
        'model_id': 'sarvam-105b',
        'note': 'Preserved evaluation path; not used by the active burn chatbot.'
    },
    'vakyansh': {
        'label': 'Vakyansh',
        'kind': 'automatic-speech-recognition',
        'model_id': 'Harveenchadha/vakyansh-wav2vec2-hindi-him-4200',
        'note': 'Hindi ASR model, not a text chat generator.'
    },
    'local': {
        'label': 'Deterministic fallback',
        'kind': 'fallback',
        'model_id': None,
        'note': 'Safe local wording fallback when Airavata is unavailable.'
    },
}

def catalog():
    return MODEL_CATALOG

def safe_model_response(model_key: str, user_message: str, draft: str) -> tuple[str, dict]:
    """Use Airavata only as a wording layer over an approved backend draft."""
    if model_key == 'local':
        return draft, {
            'model_key': 'local',
            'model_label': MODEL_CATALOG['local']['label'],
            'model_status': 'fallback'
        }

    if model_key != 'airavata':
        return draft, {
            'model_key': model_key,
            'model_label': MODEL_CATALOG.get(model_key, {}).get('label', model_key),
            'model_status': 'inactive_for_chatbot'
        }

    prompt = f'''You are Airavata, the final language/writing layer of Hinglish MedCare.
The backend has ALREADY performed the burn assessment, safety checks, triage, and
approved the facts in the response below.

Your job is ONLY to rewrite the approved response into natural, simple Indian
Hinglish/Hindi/English matching the user's language.

CRITICAL RULES:
- Do not diagnose.
- Do not add any medical fact, remedy, warning, symptom, urgency, or instruction.
- Do not remove any safety-critical instruction.
- Do not change RED/YELLOW/GREEN/UNKNOWN meaning or urgency.
- Do not invent patient details.
- Preserve the backend's questions exactly in meaning.
- Preserve WHO/source references when present.
- Keep the answer concise and easy to understand.
- Output ONLY the rewritten response.

User message:
{user_message}

APPROVED BACKEND RESPONSE:
{draft}
'''

    try:
        raw = generate('airavata', prompt).strip()
        if raw and len(raw) <= 6000:
            return raw, {
                'model_key': 'airavata',
                'model_label': MODEL_CATALOG['airavata']['label'],
                'model_status': 'generated',
                'model_id': MODEL_CATALOG['airavata']['model_id']
            }
        return draft, {
            'model_key': 'airavata',
            'model_label': MODEL_CATALOG['airavata']['label'],
            'model_status': 'invalid_output_fallback',
            'model_id': MODEL_CATALOG['airavata']['model_id']
        }
    except Exception as exc:
        log.warning('Airavata unavailable: %s', exc)
        return draft, {
            'model_key': 'airavata',
            'model_label': MODEL_CATALOG['airavata']['label'],
            'model_status': 'unavailable_fallback',
            'model_id': MODEL_CATALOG['airavata']['model_id'],
            'model_error': str(exc)[:240]
        }
