import json

# Age is collected after incident guidance; it must not block urgent first aid.
REQUIRED = ['cause_of_burn','body_part_affected','smoke_or_enclosed_space_exposure','time_since_burn','approximate_size','blistering_or_skin_appearance','pain_level','circumferential']
PRIORITY = ['cause_of_burn','body_part_affected','smoke_or_enclosed_space_exposure','time_since_burn','approximate_size','blistering_or_skin_appearance','pain_level','circumferential']
LABELS = {
    'cause_of_burn':'Burn kaise hua — garam paani/tel, aag, bijli, chemical ya kisi aur cheez se?',
    'body_part_affected':'Burn body ke kis part par hai?',
    'smoke_or_enclosed_space_exposure':'Kya smoke ya band kamre mein exposure hua tha?',
    'time_since_burn':'Burn kab hua tha — abhi, kuch ghante pehle, ya kal?',
    'approximate_size':'Area aapki hatheli se chhota hai ya bada?',
    'blistering_or_skin_appearance':'Skin sirf laal hai ya blister/chhala bhi bana hai?',
    'pain_level':'Pain kaisa hai — mild, medium ya bahut zyada?',
    'circumferential':'Kya burn poore haath, ungli ya limb ke around hai?'}
WHO_SOURCE = 'WHO Burns fact sheet (13 October 2023): https://www.who.int/news-room/fact-sheets/detail/burns'


def missing(a): return [f for f in REQUIRED if a.get(f, 'unknown') in ('unknown','',None)]
def next_question(a):
    for f in PRIORITY:
        if f in missing(a): return f, LABELS[f]
    return None, None


def assess(a, emergency=None):
    if missing(a): return 'UNKNOWN', ['assessment incomplete']
    reasons = list(emergency or [])
    if a.get('body_part_affected','') in ('face','neck','airway'): reasons.append('high-risk face/airway location')
    if a.get('cause_of_burn') in ('electrical','chemical'): reasons.append('electrical or chemical mechanism reported')
    if a.get('approximate_size') == 'larger than palm': reasons.append('area reported larger than palm')
    if a.get('circumferential') == 'yes': reasons.append('circumferential involvement reported')
    if a.get('blistering_or_skin_appearance') == 'concerning appearance': reasons.append('concerning skin appearance reported')
    if reasons: return 'RED', reasons
    if a.get('blistering_or_skin_appearance') == 'blister' or a.get('pain_level') == 'severe': return 'YELLOW', ['blistering or severe pain reported']
    return 'GREEN', ['lower urgency based on the information currently available']


def immediate_first_aid(flags=None):
    urgent = bool(flags)
    opening = 'Agar abhi bhi jal raha hai to source se door ho jaiye aur apni safety pehle rakhiye.'
    if urgent:
        opening += ' Yeh potentially serious ho sakta hai — breathing problem, face/airway involvement, smoke inhalation, electrical/chemical injury ya behoshi mein abhi emergency medical help/nearest appropriate facility lein; chat ka wait na karein.'
    return (f'{opening}\n\nWHAT TO DO NOW\n'
            '• WHO ke mutabik burn ko cool running water se thanda karein; chemical burn ho to bahut saare paani se irrigate karein.\n'
            '• Kapde/jewellery sirf tab hataayein jab skin se chipke na hon aur aapki safety theek ho.\n'
            '• Saaf cloth/sheet se cover karke appropriate medical facility tak le jaayein.\n\n'
            'WHAT TO AVOID\n'
            '• Ice, paste, oil, haldi/turmeric, raw cotton ya koi material/cream seedha na lagayein.\n'
            '• Blister na kholein. Electrical current ko pehle safely switch off karein; chemical mein gloves/safety ka dhyan rakhein.\n\n'
            f'Source: {WHO_SOURCE}\n\n'
            'Main ab current burn ki details ek-ek karke confirm karunga. Pehle: ')


def guidance(severity, reasons):
    urgency = {'RED':'Yeh case urgent medical evaluation maang sakta hai. Emergency symptoms mein abhi help lein.', 'YELLOW':'Approved guidance ke hisaab se prompt medical review consider karein, khaaskar symptoms badhne par.', 'GREEN':'Abhi di gayi information ke basis par urgency lower lagti hai, lekin symptoms monitor karein.', 'UNKNOWN':'Urgency category ke liye current incident ki kuch details abhi baaki hain.'}[severity]
    return (f'WHAT TO DO NOW\nWHO-based first aid: burn ko cool running water se thanda karein, saaf cloth/sheet se cover karein aur zarurat par appropriate medical facility jaayein.\n\nWHAT TO AVOID\nIce, paste, oil, haldi/turmeric, raw cotton ya blister kholna avoid karein.\n\nWHEN TO SEEK MEDICAL HELP\n{urgency}\n\nFOLLOW-UP\nAgar pain, redness, swelling, blistering ya koi naya symptom badhe to medical help lein.\n\nSource: {WHO_SOURCE}')


def follow_up(severity): return ('required','medical review recommended') if severity in ('RED','YELLOW') else ('required','revert back with an update if symptoms change or worsen')
