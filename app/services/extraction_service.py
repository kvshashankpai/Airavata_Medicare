import re

FIELDS = ['age','cause_of_burn','time_since_burn','first_aid_given','body_part_affected','approximate_size','blistering_or_skin_appearance','pain_level','circumferential','smoke_or_enclosed_space_exposure']

# ---------- generic yes / no helpers ----------
_YES = ['ha','haa','haan','han','yes','yeah','yep','ji','ji ha','ji haan','\u0939\u093e','\u0939\u093e\u0901','\u0939\u093e\u0902','\u0939\u0948\u0902']
_NO  = ['nahi','nai','nahin','no','nope','na','\u0928\u0939\u0940\u0902','\u0928\u0939\u0940','\u0928\u093e','ji nahi','nahi ji']


def _is_yes(t: str) -> bool:
    return any(t == x or t.startswith(x + ' ') or t.startswith(x + ',') for x in _YES)


def _is_no(t: str) -> bool:
    return any(t == x or t.startswith(x + ' ') or t.startswith(x + ',') for x in _NO)


def extract(text: str) -> dict[str, str]:
    t = text.lower().strip()
    out: dict[str, str] = {}
    # Hot liquid / oil patterns — covers pure-Hindi, pure-English, and mixed Hinglish
    if any(x in t for x in [
        'garam paani', 'hot water', 'boiling water', 'scald', '\u0917\u0930\u092e \u092a\u093e\u0928\u0940',
        'tel gir', 'tel se', 'tel ka', 'tel gira', 'tel girne',
        'oil spill', 'hot oil', '\u0917\u0930\u092e \u0924\u0947\u0932',
        'garam oil', 'oil gir', 'oil se', 'oil gira', 'oil girne',
        'paani se jal', 'tel se jal', 'oil se jal',
        'garam tel', 'garam doodh', 'hot milk', 'chai', 'hot tea',
        'steam', 'bhaap', '\u092d\u093e\u092a',
    ]):
        out['cause_of_burn'] = 'hot_liquid'
    elif any(x in t for x in ['fire', 'flame', 'aag', '\u0906\u0917', 'chulha', 'stove', 'jal gaya', '\u091c\u0932 \u0917\u092f\u093e']):
        out['cause_of_burn'] = 'flame'
    elif any(x in t for x in ['electric', 'bijli', '\u092c\u093f\u091c\u0932\u0940', 'shock']): out['cause_of_burn'] = 'electrical'
    elif any(x in t for x in ['chemical', 'acid', '\u0938\u093e\u092c\u0941\u0928']): out['cause_of_burn'] = 'chemical'
    elif any(x in t for x in ['garam cheez', 'hot object', 'contact']): out['cause_of_burn'] = 'hot_object'
    # Fallback: standalone "oil" or "tel" in a burn-context message likely means hot liquid
    elif any(x in t for x in ['oil', 'tel', '\u0924\u0947\u0932']): out['cause_of_burn'] = 'hot_liquid'

    parts = [
        ('face','face'),('\u091a\u0947\u0939\u0930\u093e','face'),('gale','neck'),('neck','neck'),
        ('haath','hand'),('hath','hand'),('hat pe','hand'),('hat par','hand'),
        ('hand','hand'),('arm','arm'),('\u092c\u093e\u0902\u0939','arm'),('pair','leg/foot'),
        ('paer','leg/foot'),('foot','foot'),('leg','leg'),('chest','chest'),
        ('pet','abdomen'),('back','back'),('finger','finger'),('ungli','finger')]
    for needle, value in parts:
        if needle in t or needle in text.lower():
            out['body_part_affected'] = value
            break

    m = re.search(r'\b(\d+)\s*(hour|hours|hr|ghanta|ghante|\u0918\u0902\u091f\u0947|\u0926\u093f\u0928|day|minute|minutes|min)', t)
    if m: out['time_since_burn'] = f'{m.group(1)} {m.group(2)} ago'
    elif any(x in t for x in ['abhi','just now','now','\u0905\u092d\u0940','abhi abhi']): out['time_since_burn'] = 'just now'
    elif any(x in t for x in ['kal','yesterday','\u0915\u0932']): out['time_since_burn'] = 'yesterday'
    elif any(x in t for x in ['kuch der pehle','thodi der pehle','some time ago','recently']): out['time_since_burn'] = 'some time ago'

    if any(x in t for x in ['blister','chhala','\u091b\u093e\u0932\u093e','phaphola','\u092b\u092b\u094b\u0932\u093e']): out['blistering_or_skin_appearance'] = 'blister'
    elif any(x in t for x in ['charred','black','white','leathery','kaala','\u0915\u093e\u0932\u093e']): out['blistering_or_skin_appearance'] = 'concerning appearance'
    elif any(x in t for x in ['red','laal','\u0932\u093e\u0932','sirf laal','lal']): out['blistering_or_skin_appearance'] = 'redness only'

    if any(x in t for x in ['bahut zyada pain','severe pain','severe','very painful','zyada dard','\u092c\u0939\u0941\u0924 \u091c\u094d\u092f\u093e\u0926\u093e \u0926\u0930\u094d\u0926','bahut dard','zyada pain','bahut pain']): out['pain_level'] = 'severe'
    elif any(x in t for x in ['medium','moderate','beech ka','thoda zyada','theek thaak']): out['pain_level'] = 'moderate'
    elif any(x in t for x in ['mild','kam pain','little pain','thoda','thoda sa','kam dard','halka']): out['pain_level'] = 'mild'

    if any(x in t for x in ['hathheli se bada','larger than palm','bada area','large area','extensive','bada','badi']): out['approximate_size'] = 'larger than palm'
    elif any(x in t for x in ['hathheli se chhota','smaller than palm','small','chhota','chhoti','thoda sa']): out['approximate_size'] = 'smaller than palm'

    if any(x in t for x in ['poore around','all around','circumferential','charo taraf','\u091a\u093e\u0930\u094b\u0902 \u0924\u0930\u092b','poora','pure']): out['circumferential'] = 'yes'
    elif any(x in t for x in ['not around','\u0928\u0939\u0940\u0902']) and any(x in t for x in ['around','poora','circum']): out['circumferential'] = 'no'

    if any(x in t for x in ['no smoke','smoke nahi','dhua nahi','\u0927\u0941\u0906\u0902 \u0928\u0939\u0940\u0902']): out['smoke_or_enclosed_space_exposure'] = 'no'
    elif any(x in t for x in ['smoke','dhua','\u0927\u0941\u0906\u0902','enclosed','band kamre','\u092c\u0902\u0926 \u0915\u092e\u0930\u0947']): out['smoke_or_enclosed_space_exposure'] = 'yes'

    if any(x in t for x in ['cooling','cool water','thande paani','first aid','first-aid']): out['first_aid_given'] = 'reported'
    m = re.search(r'\b(\d{1,3})\s*(years?|saal|\u0935\u0930\u094d\u0937)', t)
    if m: out['age'] = m.group(1)
    return {k: v for k, v in out.items() if k in FIELDS}


def context_extract(text: str, current_field: str | None) -> dict[str, str]:
    """Interpret a short user reply in the context of the question being asked.

    When the bot asks about a specific field and the user responds with a bare
    yes/no or a short contextual answer, the generic extract() will miss it.
    This function fills that gap by mapping simple answers to the field.
    """
    if not current_field:
        return {}
    t = text.lower().strip()
    out: dict[str, str] = {}

    # ---- yes / no fields ----
    if current_field == 'smoke_or_enclosed_space_exposure':
        if _is_no(t):
            out['smoke_or_enclosed_space_exposure'] = 'no'
        elif _is_yes(t):
            out['smoke_or_enclosed_space_exposure'] = 'yes'
        # "nahi kitchen mei hua tha" — contains nahi at start
        elif any(t.startswith(x) for x in _NO):
            out['smoke_or_enclosed_space_exposure'] = 'no'

    elif current_field == 'circumferential':
        if _is_no(t):
            out['circumferential'] = 'no'
        elif _is_yes(t):
            out['circumferential'] = 'yes'
        elif any(t.startswith(x) for x in _NO):
            out['circumferential'] = 'no'
        elif any(x in t for x in ['ke paas', 'near', 'sirf', 'only', 'ek side', 'one side', 'thoda sa', 'pe hai']):
            out['circumferential'] = 'no'

    # ---- pain level ----
    elif current_field == 'pain_level':
        if any(x in t for x in ['zyada', 'bahut', 'severe', 'very', 'intense', '\u092c\u0939\u0941\u0924']): out['pain_level'] = 'severe'
        elif any(x in t for x in ['medium', 'moderate', 'beech', 'theek thaak']): out['pain_level'] = 'moderate'
        elif any(x in t for x in ['mild', 'kam', 'thoda', 'halka', 'little', '\u0939\u0932\u094d\u0915\u093e']): out['pain_level'] = 'mild'

    # ---- approximate size ----
    elif current_field == 'approximate_size':
        if any(x in t for x in ['bada', 'badi', 'large', 'zyada', 'bahut']): out['approximate_size'] = 'larger than palm'
        elif any(x in t for x in ['chhota', 'chhoti', 'small', 'thoda', 'kam']): out['approximate_size'] = 'smaller than palm'

    # ---- blistering / skin appearance ----
    elif current_field == 'blistering_or_skin_appearance':
        if _is_yes(t) or any(x in t for x in ['blister', 'chhala', 'phaphola']): out['blistering_or_skin_appearance'] = 'blister'
        elif _is_no(t): out['blistering_or_skin_appearance'] = 'redness only'
        elif any(x in t for x in ['red', 'laal', 'lal', 'sirf']): out['blistering_or_skin_appearance'] = 'redness only'
        elif any(x in t for x in ['black', 'kaala', 'white', 'charred']): out['blistering_or_skin_appearance'] = 'concerning appearance'

    # ---- time since burn ----
    elif current_field == 'time_since_burn':
        if any(x in t for x in ['abhi', 'just', 'now', '\u0905\u092d\u0940']): out['time_since_burn'] = 'just now'
        elif any(x in t for x in ['kal', 'yesterday', '\u0915\u0932']): out['time_since_burn'] = 'yesterday'
        m = re.search(r'(\d+)\s*(hour|hours|hr|ghanta|ghante|min|minute|minutes|\u0926\u093f\u0928|day)', t)
        if m: out['time_since_burn'] = f'{m.group(1)} {m.group(2)} ago'

    return {k: v for k, v in out.items() if k in FIELDS}


def emergency_flags(text: str) -> list[str]:
    t = text.lower()
    flags = []
    if any(x in t for x in ['breath','saans nahi','\u0938\u093e\u0902\u0938 \u0928\u0939\u0940\u0902','difficulty breathing']): flags.append('difficulty breathing')
    smoke_denied = any(x in t for x in ['no smoke','smoke nahi','dhua nahi','\u0927\u0941\u0906\u0902 \u0928\u0939\u0940\u0902'])
    if not smoke_denied and any(x in t for x in ['smoke','dhua','\u0927\u0941\u0906\u0902','inhal']): flags.append('smoke/inhalation exposure')
    if any(x in t for x in ['face','gale','neck','airway','\u092e\u0941\u0902\u0939','\u091a\u0947\u0939\u0930\u093e']): flags.append('face/airway involvement')
    if any(x in t for x in ['unconscious','behosh','\u092c\u0947\u0939\u094b\u0936']): flags.append('unconsciousness')
    if any(x in t for x in ['electric','bijli','\u092c\u093f\u091c\u0932\u0940','chemical','acid']): flags.append('electrical/chemical mechanism')
    return flags


def is_burn_message(text: str) -> bool:
    t = text.lower()
    return any(x in t for x in ['burn','burning','jal','\u091c\u0932\u093e','\u091c\u0932','scald','garam paani','hot water','oil','tel','\u0906\u0917','fire'])


def patient_details(text: str) -> dict[str, str]:
    """Parse only explicit details when the workflow has reached identity collection."""
    t = text.strip()
    result: dict[str, str] = {}
    age = re.search(r'\b(\d{1,3})\s*(?:years?|saal|\u0935\u0930\u094d\u0937)?\b', t.lower())
    if age and 0 <= int(age.group(1)) <= 130: result['age'] = age.group(1)
    cleaned = re.sub(r'\b\d{1,3}\s*(?:years?|saal|\u0935\u0930\u094d\u0937)?\b', '', t, flags=re.I).strip(' ,.-')
    if cleaned and not result.get('age') and len(cleaned.split()) <= 5: result['name'] = cleaned
    elif cleaned and result.get('age'): result['name'] = cleaned
    return result
