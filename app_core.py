"""
Livestock Health Assistant - Core Logic
-----------------------------------------
This file does 3 things:
1. Loads our knowledge base (knowledge_base.json)
2. Matches a farmer's symptom description against it
3. Sends the matched info + question to the local AI model (via Ollama)
   so it can respond in clear, natural language

Run this file directly to test it in the terminal before we build the
Streamlit interface on top of it.
"""

import json
import ollama

MODEL_NAME = "phi3:mini"  # change to "gemma2:2b" if you picked that one


def load_knowledge_base(path="knowledge_base.json"):
    """Reads the knowledge base JSON file into a Python list."""
    with open(path, "r") as f:
        return json.load(f)


def find_matches(symptom_text, knowledge_base):
    """
    Very simple keyword matching: checks if any keyword from each
    knowledge base entry appears in what the farmer typed.
    Returns a list of matching entries (best matches first).
    """
    symptom_text_lower = symptom_text.lower()
    matches = []

    for entry in knowledge_base:
        match_count = sum(
            1 for keyword in entry["keywords"] if keyword in symptom_text_lower
        )
        if match_count > 0:
            matches.append((match_count, entry))

    # Sort so entries with more keyword matches come first
    matches.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in matches]


def build_prompt(symptom_text, matches):
    """
    Builds the text we send to the AI model. We give it the farmer's
    question PLUS the relevant knowledge base entries, so it answers
    using OUR trusted information instead of making things up.
    """
    if not matches:
        prompt = f"""You are a helpful assistant for smallholder farmers in Ethiopia.
A farmer describes a symptom below. Our knowledge base has NO matching condition for this.

Farmer's description: "{symptom_text}"

You must respond with ONLY this exact message, filled in naturally:
Say you don't have specific information on this symptom in your knowledge base,
and that they should consult a local veterinarian, especially if the animal seems
to be in pain or distress. Do NOT guess a diagnosis. Do NOT invent advice.
Keep it to 2 sentences. Output nothing else after your answer."""
        return prompt

    context_parts = []
    for entry in matches[:2]:  # use top 2 matches max
        context_parts.append(
            f"- Condition: {entry['condition']} (animal: {entry['animal']})\n"
            f"  Advice: {entry['advice']}\n"
            f"  Emergency: {'YES' if entry['emergency'] else 'No'}"
        )
    context = "\n".join(context_parts)

    prompt = f"""You are a helpful assistant for smallholder farmers in Ethiopia.
A farmer describes a symptom. Use ONLY the information below to answer.
Be clear, short, and practical. If it's an emergency, say so clearly at the start.
Do not add anything after your answer - no extra examples, no new instructions, nothing.

Farmer's description: "{symptom_text}"

Relevant information:
{context}

Give a short, friendly response (max 4 sentences) with practical next steps, then stop."""
    return prompt


def get_response(symptom_text, knowledge_base):
    """Full pipeline: match symptoms, build prompt, call the AI model."""
    matches = find_matches(symptom_text, knowledge_base)
    prompt = build_prompt(symptom_text, matches)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={"num_predict": 200},  # caps response length so it can't ramble on
    )
    return response["message"]["content"]


if __name__ == "__main__":
    # Simple terminal test loop
    kb = load_knowledge_base()
    print("Livestock Health Assistant (test mode). Type 'quit' to exit.\n")

    while True:
        user_input = input("Describe the symptom: ")
        if user_input.lower() == "quit":
            break
        answer = get_response(user_input, kb)
        print(f"\nAssistant: {answer}\n")
