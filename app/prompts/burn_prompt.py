def build_burn_prompt(user_message: str, assessment: dict) -> str:
    return f'''Extract only explicitly stated burn facts from this Hinglish/English message. Never guess. Return JSON.\nMessage: {user_message}\nCurrent assessment: {assessment}'''
