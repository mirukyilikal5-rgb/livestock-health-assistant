"""
Livestock Health Assistant - Core Logic (Week 5: structured responses)
---------------------------------------------------------------------------
Key design decision: the structured sections (causes, actions, warning
signs, recommendation, follow-up questions) are CURATED DATA from the
knowledge base, not AI-generated. Small local models are unreliable at
consistently following formatting instructions (confirmed via testing -
they ramble, ignore "stop" instructions, or drop sections). Curated data
guarantees the same reliable structure every time.

The AI model is still used LIVE, for a short one-sentence empathetic
opener in English - so the assistant still feels conversational and is
genuinely AI-generated, without risking the safety-critical structured
content on the model's formatting reliability.

Amharic responses skip the AI entirely (tested and confirmed phi3:mini's
Amharic generation is unusable) - everything is curated, human-reviewed text.
"""

import json
import re
import ollama

MODEL_NAME = "phi3:mini"
VISION_MODEL_NAME = "moondream"  # separate model - phi3:mini cannot see images

STOPWORDS = {
    "a", "an", "the", "and", "or", "is", "are", "was", "were", "it", "its",
    "this", "that", "in", "on", "at", "up", "down", "not", "no", "all",
    "of", "to", "for", "with", "has", "have", "had", "i", "you", "your",
    "my", "won't", "wont", "can't", "cant", "be", "been", "will", "looks",
    "look", "lot", "a lot",
}

WEAK_WORDS = {"swollen", "pain", "painful", "hurts", "sick", "distress"}

MIN_MEANINGFUL_OVERLAP = 1


def load_knowledge_base(path="knowledge_base.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def meaningful_words(text):
    """Splits text into words and removes stopwords and overly generic words."""
    words = set(text.lower().split())
    return words - STOPWORDS - WEAK_WORDS


def find_matches(symptom_text, knowledge_base):
    """
    Fuzzy matching that checks BOTH English and Amharic keyword lists,
    so a farmer can describe symptoms in either language.
    """
    input_words = meaningful_words(symptom_text)
    matches = []

    for entry in knowledge_base:
        all_keywords = entry.get("keywords", []) + entry.get("keywords_am", [])
        best_overlap = 0
        for keyword in all_keywords:
            keyword_words = meaningful_words(keyword)
            overlap = len(input_words & keyword_words)
            best_overlap = max(best_overlap, overlap)

        if best_overlap >= MIN_MEANINGFUL_OVERLAP:
            matches.append((best_overlap, entry))

    matches.sort(key=lambda x: x[0], reverse=True)
    # Returns (overlap_score, entry) tuples so callers can judge match confidence,
    # not just the entry itself.
    return matches


def get_confidence_label(overlap, language="English"):
    """
    Deterministic (not AI-guessed) confidence rating based on how many
    meaningful keyword words matched. More overlap = more specific match.
    """
    if overlap >= 3:
        level_en, emoji, reason_en = "High", "🟢", "Matched multiple specific symptom details."
        reason_am = "ብዙ የተለዩ የምልክት ዝርዝሮች ተዛማጅነት ተገኝቷል።"
        level_am = "ከፍተኛ"
    elif overlap == 2:
        level_en, emoji, reason_en = "Medium", "🟡", "Matched some symptom details."
        reason_am = "የተወሰኑ የምልክት ዝርዝሮች ተዛማጅነት ተገኝቷል።"
        level_am = "መካከለኛ"
    else:
        level_en, emoji, reason_en = "Low", "🟠", "Limited information provided — consider adding more detail."
        reason_am = "የቀረበው መረጃ ውስን ነው — ተጨማሪ ዝርዝር ቢጨምሩ ይመከራል።"
        level_am = "ዝቅተኛ"

    if language == "Amharic":
        return f"**እርግጠኝነት፡** {emoji} {level_am}\n*{reason_am}*"
    return f"**Confidence:** {emoji} {level_en}\n*{reason_en}*"


PREVENTION_TIPS = [
    ("Always provide clean drinking water and clean feeding areas.",
     "ሁልጊዜ ንጹህ የመጠጥ ውሃ እና ንጹህ የመመገቢያ ቦታ ያቅርቡ።"),
    ("Deworm your animals on a regular schedule to prevent parasite buildup.",
     "የትል ጫናን ለመከላከል እንስሳትዎን በመደበኛነት ያድልቁ።"),
    ("Keep housing dry and well-ventilated to reduce respiratory illness.",
     "የመተንፈሻ በሽታን ለመቀነስ መኖሪያውን ደረቅ እና አየር በደንብ የሚዘዋወርበት ያድርጉት።"),
    ("Quarantine new animals for at least 2 weeks before introducing them to the herd.",
     "አዲስ እንስሳትን ወደ መንጋው ከማስገባትዎ በፊት ቢያንስ ለ2 ሳምንታት ለይተው ያቆዩ።"),
    ("Vaccinate on schedule - prevention is far cheaper than treatment.",
     "በጊዜው ክትባት ይስጡ - መከላከል ከሕክምና በጣም ርካሽ ነው።"),
    ("Inspect feet and udders regularly to catch problems early.",
     "ችግሮችን ቀድሞ ለመያዝ እግሮችን እና ጡቶችን በመደበኛነት ይመልከቱ።"),
    ("Avoid sudden feed changes - introduce new feed gradually.",
     "ድንገተኛ የምግብ ለውጥ ያስወግዱ - አዲስ ምግብን ቀስ በቀስ ያስተዋውቁ።"),
    ("Control ticks and flies regularly to prevent disease spread.",
     "በሽታ እንዳይተላለፍ መዥገሮችን እና ዝንቦችን በመደበኛነት ይቆጣጠሩ።"),
]


def get_daily_tip(language="English"):
    """
    Rotates by day-of-year so it changes daily but stays consistent within
    a day (not random on every reload). Curated list, not AI-generated.
    """
    import datetime
    idx = datetime.datetime.now().timetuple().tm_yday % len(PREVENTION_TIPS)
    tip_en, tip_am = PREVENTION_TIPS[idx]
    return tip_am if language == "Amharic" else tip_en


def build_opener_prompt(symptom_text, condition, animal_info=None):
    """
    Short prompt for a ONE-sentence empathetic opener only - no advice,
    no diagnosis, no structure. The real content comes from curated data.
    """
    context = f" ({animal_info})" if animal_info else ""
    return f"""You are a warm, brief assistant for smallholder farmers in Ethiopia.
The farmer describes a symptom{context}: "{symptom_text}"
It has been matched to: {condition}

Write EXACTLY ONE short, warm sentence acknowledging their situation.
Do NOT give advice, causes, or a diagnosis explanation - that comes separately.
Do NOT add anything after the one sentence."""


def build_no_match_prompt(symptom_text):
    return f"""You are a helpful assistant for smallholder farmers in Ethiopia.
Our knowledge base has NO matching condition for this symptom.

Farmer's description: "{symptom_text}"

Respond with exactly 2 sentences: say you don't have specific information on
this symptom, and recommend consulting a local veterinarian, especially if
the animal seems to be in pain or distress. Do NOT guess a diagnosis.
Output nothing else after your 2 sentences."""


def clean_response(text, max_sentences=4):
    """Cuts off leaked text and caps the reply to a handful of real sentences."""
    cutoff_patterns = [r"##", r"\bInstruction\b", r"\n\n\n", r"\nAdvice:", r"\nStop\b"]
    for pattern in cutoff_patterns:
        match = re.search(pattern, text)
        if match:
            text = text[:match.start()]
    text = text.strip()

    sentences = re.split(r"(?<=[.!?።])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    while len(sentences) > 1 and len(sentences[-1].split()) < 3:
        sentences.pop()

    return " ".join(sentences[:max_sentences]).strip()


def format_structured_response(entry, language="English"):
    """
    Builds the structured markdown response (Possible Causes, What You Can
    Do Now, Warning Signs, Recommendation, Follow-Up Questions) directly
    from curated knowledge base data - reliable formatting every time.
    """
    if language == "Amharic":
        causes = entry.get("causes_am", [])
        actions = entry.get("actions_am", [])
        warnings = entry.get("warning_signs_am", [])
        recommendation = entry.get("recommendation_am", "")
        follow_ups = entry.get("follow_up_questions_am", [])
        headers = {
            "causes": "ሊሆኑ የሚችሉ ምክንያቶች",
            "actions": "አሁን ማድረግ የሚችሉት",
            "warnings": "የማስጠንቀቂያ ምልክቶች",
            "recommendation": "ምክር",
            "follow_ups": "የሚረዱ ጥያቄዎች",
        }
    else:
        causes = entry.get("causes", [])
        actions = entry.get("actions", [])
        warnings = entry.get("warning_signs", [])
        recommendation = entry.get("recommendation", "")
        follow_ups = entry.get("follow_up_questions", [])
        headers = {
            "causes": "Possible Causes",
            "actions": "What You Can Do Now",
            "warnings": "Warning Signs",
            "recommendation": "Recommendation",
            "follow_ups": "Questions That Can Help",
        }

    parts = []
    if causes:
        parts.append(f"**{headers['causes']}**\n" + "\n".join(f"- {c}" for c in causes))
    if actions:
        parts.append(f"**{headers['actions']}**\n" + "\n".join(f"✅ {a}" for a in actions))
    if warnings:
        parts.append(f"**{headers['warnings']}**\n" + "\n".join(f"🚨 {w}" for w in warnings))
    if recommendation:
        parts.append(f"**{headers['recommendation']}**\n{recommendation}")
    if follow_ups:
        parts.append(f"**{headers['follow_ups']}**\n" + "\n".join(f"❓ {q}" for q in follow_ups))

    return "\n\n".join(parts)


# Fixed Amharic fallback text for symptoms not in the knowledge base -
# hard-coded (not AI-generated), so it's always correct.
NO_MATCH_TEXT_AM = (
    "ይህን ምልክት በእውቀት ቋቴ ውስጥ የለም። እባክዎ የአካባቢዎን የእንስሳት ሐኪም ያማክሩ፣ "
    "በተለይ እንስሳው ህመም ወይም ምቾት ማጣት የሚያሳይ ከሆነ።"
)


def _call_ai(prompt, num_predict=200, temperature=0.3, max_sentences=4):
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={"num_predict": num_predict, "temperature": temperature},
    )
    return clean_response(response["message"]["content"], max_sentences=max_sentences)


def analyze_image(image_bytes, animal_type=None):
    """
    Uses a separate VISION model to describe what's visible in a photo -
    it does NOT diagnose. The description it produces gets run through the
    same find_matches()/get_response() pipeline as typed text, so the same
    safety layer (emergency detection, curated advice) always applies.

    Returns a short English description string, e.g.
    "swollen, red, watery right eye with discharge"
    """
    animal_context = f" of a {animal_type}" if animal_type else ""
    prompt = (
        f"You are looking at a photo{animal_context} for veterinary purposes. "
        "Describe ONLY the visible physical symptoms in plain, simple English "
        "(e.g. swelling, redness, discharge, wounds, skin condition, posture). "
        "Do NOT diagnose a condition or name a disease. Do NOT guess age or breed. "
        "Keep it to one short sentence, purely descriptive."
    )
    response = ollama.chat(
        model=VISION_MODEL_NAME,
        messages=[{"role": "user", "content": prompt, "images": [image_bytes]}],
        options={"num_predict": 80, "temperature": 0.2},
    )
    return clean_response(response["message"]["content"], max_sentences=1)


def get_response(symptom_text, knowledge_base, language="English", animal_info=None):
    """
    Full pipeline. For a matched condition: a short live-AI opener sentence
    (English only) + curated structured sections (causes/actions/warnings/
    recommendation/follow-ups) in the requested language. For no match:
    an honest fallback (AI-generated for English, curated for Amharic).

    animal_info: optional string like "Age: 2 years, Sex: Female" - used
    only to give the AI opener a bit more context, never affects matching.
    """
    matches = find_matches(symptom_text, knowledge_base)  # list of (overlap, entry)
    best_overlap, best_match = matches[0] if matches else (0, None)
    is_emergency = best_match is not None and best_match.get("emergency", False)

    # --- No match: honest fallback ---
    if best_match is None:
        if language == "Amharic":
            return NO_MATCH_TEXT_AM
        return _call_ai(build_no_match_prompt(symptom_text), num_predict=100, max_sentences=2)

    # --- Matched: confidence + opener (English only, live AI) + curated structured content ---
    confidence_line = get_confidence_label(best_overlap, language=language)
    structured = format_structured_response(best_match, language=language)

    if language == "Amharic":
        body = f"{confidence_line}\n\n{structured}"
    else:
        condition = best_match["condition"]
        opener_prompt = build_opener_prompt(symptom_text, condition, animal_info)
        opener = _call_ai(opener_prompt, num_predict=60, max_sentences=1)
        body = f"{opener}\n\n{confidence_line}\n\n{structured}"

    if is_emergency:
        if language == "Amharic":
            condition_label = best_match.get("condition_am", best_match["condition"])
            warning = f"🚨 አደጋ - ምናልባት {condition_label}። በተቻለ ፍጥነት የእንስሳት ሐኪም ያማክሩ።"
        else:
            warning = f"🚨 EMERGENCY - possible {best_match['condition']}. Seek a vet as soon as possible."
        return f"{warning}\n\n{body}"

    return body


if __name__ == "__main__":
    kb = load_knowledge_base()
    print("Livestock Health Assistant (test mode). Type 'quit' to exit.\n")
    lang_choice = input("Response language - type 'en' or 'am': ").strip().lower()
    language = "Amharic" if lang_choice == "am" else "English"

    while True:
        user_input = input("Describe the symptom: ")
        if user_input.lower() == "quit":
            break
        answer = get_response(user_input, kb, language=language)
        print(f"\nAssistant:\n{answer}\n")
