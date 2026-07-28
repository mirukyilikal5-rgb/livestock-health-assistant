# livestock-health-assistant-offline AI for smallholder farmers
An offline AI-powered assistant that helps smallholder farmers in Ethiopia identify common livestock symptoms and get first-response guidance — no internet connection required.

Built for the **Africa Deep Tech Challenge 2026**.

## Why offline?

Rural connectivity in Ethiopia is inconsistent, but livestock health decisions can't wait. This app runs entirely on-device using a quantized local LLM, so a farmer or extension worker can get guidance anywhere — no data cost, no signal required.

## How it works

1. Farmer describes symptoms (typed or via checklist) in the Streamlit interface
2. The app matches symptoms against a curated veterinary knowledge base
3. A local LLM (via [Ollama](https://ollama.com)) generates a clear, conversational response grounded in that knowledge base
4. Emergency symptoms trigger an immediate "see a vet now" flag, bypassing the model entirely

## Tech stack

- **Model:** [Gemma 2 2B / Phi-3-mini] running locally via Ollama
- **Backend:** Python
- **Interface:** Streamlit
- **Knowledge base:** Structured JSON of symptoms → likely conditions → recommended actions

## Setup

```bash
# 1. Install Ollama and pull the model
ollama pull gemma2:2b   # or phi3:mini

# 2. Clone and install dependencies
git clone https://github.com/<your-username>/livestock-health-assistant.git
cd livestock-health-assistant
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

No internet connection needed after setup — the model and app run fully local.

## Demo

*[<img width="1920" height="1080" alt="Screenshot (95)" src="https://github.com/user-attachments/assets/8475cfac-0b25-4a18-8c51-656d419055d3" />
]

*

## Status

🚧 In active development for Africa Deep Tech Challenge 2026 (submission: Aug 25, 2026)

- [x] Model selection & benchmarking
- [x] Knowledge base v1
- [ ] Streamlit UI
- [ ] Offline packaging & testing
- [ ] User testing

## Disclaimer

This tool provides preliminary guidance only and does not replace professional veterinary care.



