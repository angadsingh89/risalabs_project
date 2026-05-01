# Coverage Review Assistant

Coverage review automation using a multi-agent Claude AI pipeline.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Enter your Anthropic API key in the sidebar for live mode, or enable demo mode to run without a key.

## Data Sources
- **Clinical Cases**: MTSamples-style real medical transcriptions (20 cases, 4 specialties)
- **Coverage Guidelines**: CMS LCD criteria for 5 procedures

## Agents
1. **Chart Reviewer** — Extracts structured clinical facts
2. **Criteria Mapper** — Maps facts to coverage criteria (MET / NOT MET / INSUFFICIENT)
3. **Decision Engine** — APPROVED / DENIED / PEND with confidence score
4. **Appeal Advisor** — Documentation gaps, appeal strategy, peer-to-peer talking points

## Deploy to Streamlit Cloud
1. Push to GitHub
2. Go to share.streamlit.io
3. Connect repo → set `app.py` as entry point
4. Add `ANTHROPIC_API_KEY` in Secrets
