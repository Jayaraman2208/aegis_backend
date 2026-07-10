"""
Lightweight intent-matching bot for the Ask Aegis assistant.

This keeps the same behaviour as the frontend prototype but runs
server-side so the conversation can be persisted, localized, and later
swapped for a real NLP/LLM backend without changing the API contract.
"""

RULES = [
    (('hospital', 'er', 'emergency room'), 'find_hospital',
     "Nearest ER: St. Xavier General, 0.8km away, currently accepting patients. "
     "Want me to start walking directions?"),
    (('translate', 'help', 'phrase'), 'translate_phrase',
     '"I need help" in the local language: "Necesito ayuda." '
     "Tap and hold to hear the pronunciation."),
    (('safe', 'area', 'zone'), 'area_safety',
     "You're in a green zone right now — score 88, well-lit and busy tonight. "
     "One area two blocks north is under caution after 8pm."),
    (('police', 'station', 'report'), 'find_police',
     "Nearest station: Central Precinct, 1.1km, open 24/7. "
     "I can also help you file a report right here."),
    (('pharmacy', 'medicine', 'medication'), 'find_pharmacy',
     "Two 24-hour pharmacies within 1km. Closest is Lumen Pharmacy, 350m away."),
    (('embassy', 'consulate', 'passport'), 'find_embassy',
     "Your nearest consulate is 2.3km away and open until 5pm today. "
     "I've saved the address and phone number to your profile."),
]

DEFAULT_REPLY = (
    "Got it — I'll keep that in mind. You can also ask me about nearby "
    "hospitals, safe routes, translations, or filing a police report any time."
)


def get_bot_reply(text: str):
    """Return (reply_text, intent) for a given user message."""
    lowered = text.lower()
    for keywords, intent, reply in RULES:
        if any(k in lowered for k in keywords):
            return reply, intent
    return DEFAULT_REPLY, 'general'
