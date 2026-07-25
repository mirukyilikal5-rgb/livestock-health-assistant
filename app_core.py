"""
Livestock Health Assistant - Core Logic (Week 2, revised)
-------------------------------------------------------------
Fixes from batch testing:
1. Stopword filtering - short/common words (the, at, up, its...) no
   longer cause false matches on their own.
2. Only the single BEST match is used, not top-2 - prevents mixing
   unrelated conditions into one confusing answer.
3. Response is truncated to a safe max length and cut off if the
   model starts leaking unrelated text (e.g. "## Instruction...").
"""

import json
import re
import ollama

MODEL_NAME = "phi3:mini"

# Common short words that shouldn't count as a "meaningful" match on their own
STOPWORDS = {
    "a", "an", "the", "and", "or", "is", "are", "was", "were", "it", "its",
    "this", "that", "in", "on", "at", "up", "down", "not", "no", "all",
    "of", "to", "for", "with", "has", "have", "had", "i", "you", "your",
    "my", "won't", "wont", "can't", "cant", "be", "been", "will", "looks",
    "look", "lot", "a lot",
}

# Words that describe a symptom in general terms but are too generic to
# reliably identify a SPECIFIC condition on their own (e.g. "swollen" shows
# up across bloat, mastitis, foot rot, eye infection...). These are ignored
# unless paired with a more specific word (e.g. "swollen" + "belly").
WEAK_WORDS = {"swollen", "pain", "painful", "hurts", "sick", "distress"}

# Minimum number of MEANINGFUL (non-stopword, non-weak) words that must
# overlap for a match to count. Raising this reduces false positives.
MIN_MEANINGFUL_OVERLAP = 1


def load_knowledge_base(path="knowledge_base.json"):
    with open(path, "r") as f:
        return json.load(f)


def meaningful_words(text):
    """Splits text into words and removes stopwords and overly generic words."""
    words = set(text.lower().split())
    return words - STOPWORDS - WEAK_WORDS


def find_matches(symptom_text, knowledge_base):
    """
    Fuzzy matching using only meaningful (non-stopword) words, so
    common words like 'at' or 'the' can't trigger a false match.
    Returns matches sorted best-first.
    """
    input_words = meaningful_words(symptom_text)
    matches = []

    for entry in knowledge_base:
        best_overlap = 0
        for keyword in entry["keywords"]:
            keyword_words = meaningful_words(keyword)
            overlap = len(input_words & keyword_words)
            best_overlap = max(best_overlap, overlap)

        if best_overlap >= MIN_MEANINGFUL_OVERLAP:
            matches.append((best_overlap, entry))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in matches]


def build_prompt(symptom_text, best_match):
    """
    Builds the prompt using ONLY the single best match (not multiple),
    so the model can't blend unrelated conditions together.
    """
    if best_match is None:
        return f"""You are a helpful assistant for smallholder farmers in Ethiopia.
Our knowledge base has NO matching condition for this symptom.

Farmer's description: "{symptom_text}"

Respond with exactly 2 sentences: say you don't have specific information on
this symptom, and recommend consulting a local veterinarian, especially if
the animal seems to be in pain or distress. Do NOT guess a diagnosis.
Output nothing else after your 2 sentences."""

    return f"""You are a helpful assistant for smallholder farmers in Ethiopia.
Use ONLY the information below to answer. Be clear, short, and practical.
Do not add anything after your answer - no extra examples, no new instructions,
no headings, nothing else.

Farmer's description: "{symptom_text}"

Condition: {best_match['condition']} (animal: {best_match['animal']})
Advice: {best_match['advice']}

Give a short, friendly response (max 3 sentences) with practical next steps, then stop completely."""


def clean_response(text, max_sentences=4):
    """
    Safety net: cuts off anything past a normal answer (headings, stray
    labels, markdown separators), then caps the reply to a handful of
    real sentences and drops short leaked fragments like a lone "Stop".
    """
    cutoff_patterns = [r"##", r"\bInstruction\b", r"\n\n\n", r"\nAdvice:", r"\nStop\b"]
    for pattern in cutoff_patterns:
        match = re.search(pattern, text)
        if match:
            text = text[:match.start()]
    text = text.strip()

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Drop trailing fragments that are too short to be a real sentence
    while len(sentences) > 1 and len(sentences[-1].split()) < 3:
        sentences.pop()

    return " ".join(sentences[:max_sentences]).strip()


def get_response(symptom_text, knowledge_base):
    """
    Full pipeline: find best match -> check emergency in CODE ->
    build prompt -> call AI -> clean output -> prepend emergency warning.
    """
    matches = find_matches(symptom_text, knowledge_base)
    best_match = matches[0] if matches else None
    is_emergency = best_match is not None and best_match.get("emergency", False)

    prompt = build_prompt(symptom_text, best_match)
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={"num_predict": 150, "temperature": 0.3},
    )
    ai_text = clean_response(response["message"]["content"])

    if is_emergency:
        condition = best_match["condition"]
        return f"EMERGENCY - possible {condition}. Seek a vet as soon as possible.\n\n{ai_text}"
    return ai_text


if __name__ == "__main__":
    kb = load_knowledge_base()
    print("Livestock Health Assistant (test mode). Type 'quit' to exit.\n")

    while True:
        user_input = input("Describe the symptom: ")
        if user_input.lower() == "quit":
            break
        answer = get_response(user_input, kb)
        print(f"\nAssistant: {answer}\n")
