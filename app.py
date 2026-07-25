"""
Livestock Health Assistant - Streamlit Interface (Week 3)
--------------------------------------------------------------
This is the visual app. It reuses all the logic from app_core.py
(matching, safety checks, AI calls) and just adds a proper UI on top.

Run with: streamlit run app.py
"""

import streamlit as st
from app_core import load_knowledge_base, get_response

# --- Page setup ---
st.set_page_config(page_title="Livestock Health Assistant", page_icon="🐄")

st.title("🐄 Livestock Health Assistant")
st.caption("Offline AI guidance for smallholder farmers — not a replacement for a vet.")

# --- Load knowledge base once and keep it in memory ---
if "kb" not in st.session_state:
    st.session_state.kb = load_knowledge_base()

# --- Keep chat history across interactions ---
if "history" not in st.session_state:
    st.session_state.history = []  # list of (role, text) tuples

# --- Sidebar: animal type selector (helps the farmer describe things faster) ---
st.sidebar.header("Animal Details")
animal_type = st.sidebar.selectbox(
    "What animal is this about?",
    ["Cattle", "Goat", "Poultry", "Other / Not sure"],
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ This tool gives general guidance only. Always consult a local "
    "veterinarian for serious or persistent symptoms."
)

# --- Display past conversation ---
for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

# --- Input box at the bottom (chat-style) ---
user_input = st.chat_input("Describe the symptom you're seeing...")

if user_input:
    # Prepend animal type to the symptom text so matching has more context
    full_symptom_text = f"[{animal_type}] {user_input}"

    # Show the farmer's message immediately
    st.session_state.history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get the AI response
    with st.chat_message("assistant"):
        with st.spinner("Checking..."):
            answer = get_response(full_symptom_text, st.session_state.kb)

        # Style emergencies differently so they stand out visually
        if answer.startswith("EMERGENCY"):
            st.error(answer)
        else:
            st.markdown(answer)

    st.session_state.history.append(("assistant", answer))
