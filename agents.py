import anthropic
import json
import streamlit as st

client = None


def init_client(api_key: str):
    global client
    client = anthropic.Anthropic(api_key=api_key)


def run_agent(agent_name: str, system_prompt: str, user_message: str) -> str:
    """Run a single agent and return its output."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def agent_1_chart_reviewer(transcription: str, procedure: str) -> dict:
    system = """You are Agent 1: Clinical Chart Reviewer. Your job is to extract structured clinical facts from a patient transcription that are relevant to a prior authorization request.

Extract and return a JSON object with these exact keys:
{
  "diagnosis": "primary diagnosis",
  "procedure_requested": "what is being requested",
  "imaging_results": "relevant imaging findings or 'None documented'",
  "conservative_treatments": ["list of treatments tried with duration"],
  "duration_of_symptoms": "how long patient has had symptoms",
  "functional_impairment": "documented functional limitations",
  "contraindications_noted": "any contraindications mentioned or 'None documented'",
  "red_flags": ["any urgent/emergency findings"],
  "missing_information": ["list of clinically relevant info that is absent from the note"]
}

Return ONLY valid JSON. No preamble, no explanation."""

    user = f"""Procedure being requested: {procedure}

Patient transcription:
{transcription}"""

    result = run_agent("Chart Reviewer", system, user)
    try:
        return json.loads(result)
    except Exception:
        return {"raw_output": result}


def agent_2_criteria_mapper(chart_data: dict, guidelines: list, procedure_name: str) -> dict:
    system = """You are Agent 2: Coverage Criteria Mapper. Given extracted chart data and coverage criteria, evaluate each criterion.

Return a JSON object:
{
  "criteria_results": [
    {
      "criterion": "the criterion text",
      "status": "MET" | "NOT MET" | "INSUFFICIENT INFO",
      "evidence": "specific quote or data point from chart that supports this assessment",
      "notes": "brief clinical reasoning"
    }
  ],
  "met_count": number,
  "not_met_count": number,
  "insufficient_count": number
}

Return ONLY valid JSON."""

    user = f"""Procedure: {procedure_name}

Coverage criteria to evaluate:
{json.dumps(guidelines, indent=2)}

Extracted chart data:
{json.dumps(chart_data, indent=2)}"""

    result = run_agent("Criteria Mapper", system, user)
    try:
        return json.loads(result)
    except Exception:
        return {"raw_output": result}


def agent_3_decision_engine(criteria_results: dict, procedure_name: str) -> dict:
    system = """You are Agent 3: Prior Authorization Decision Engine. Based on criteria mapping results, make a coverage determination.

Return a JSON object:
{
  "decision": "APPROVED" | "DENIED" | "PEND FOR ADDITIONAL INFO",
  "confidence": number between 0-100,
  "primary_reason": "one sentence primary rationale",
  "supporting_reasons": ["up to 3 bullet reasons"],
  "denial_codes": ["relevant denial reason codes if denied, e.g. 'CO-197: Precertification required'"],
  "clinical_basis": "clinical guideline or LCD reference supporting this decision"
}

Return ONLY valid JSON."""

    user = f"""Procedure: {procedure_name}

Criteria evaluation results:
{json.dumps(criteria_results, indent=2)}"""

    result = run_agent("Decision Engine", system, user)
    try:
        return json.loads(result)
    except Exception:
        return {"raw_output": result}


def agent_4_appeal_advisor(
    decision: dict, criteria_results: dict, chart_data: dict, procedure_name: str
) -> dict:
    system = """You are Agent 4: Appeal & Documentation Advisor. Your role is to help providers understand what additional documentation or actions could strengthen a PA request or support an appeal.

Return a JSON object:
{
  "immediate_actions": ["specific things the provider can do RIGHT NOW to strengthen this request"],
  "documentation_gaps": ["specific missing documents that if submitted could change the decision"],
  "appeal_likelihood": "HIGH" | "MODERATE" | "LOW",
  "appeal_strategy": "one paragraph strategic advice for appealing if denied",
  "peer_to_peer_recommended": true | false,
  "peer_to_peer_talking_points": ["3-4 clinical talking points for a peer-to-peer review call"],
  "alternative_options": ["alternative procedures or treatment paths if this gets denied permanently"]
}

Return ONLY valid JSON."""

    user = f"""Procedure: {procedure_name}
Decision: {decision.get('decision', 'UNKNOWN')}

Unmet criteria:
{json.dumps([c for c in criteria_results.get('criteria_results', []) if c.get('status') != 'MET'], indent=2)}

Chart summary:
{json.dumps(chart_data, indent=2)}"""

    result = run_agent("Appeal Advisor", system, user)
    try:
        return json.loads(result)
    except Exception:
        return {"raw_output": result}


def run_full_pipeline(transcription: str, procedure: str, guidelines: list, guideline_name: str):
    """Run all 4 agents sequentially, yielding results."""

    # Agent 1
    chart_data = agent_1_chart_reviewer(transcription, procedure)
    yield "agent_1", chart_data

    # Agent 2
    criteria_results = agent_2_criteria_mapper(chart_data, guidelines, guideline_name)
    yield "agent_2", criteria_results

    # Agent 3
    decision = agent_3_decision_engine(criteria_results, guideline_name)
    yield "agent_3", decision

    # Agent 4
    advice = agent_4_appeal_advisor(decision, criteria_results, chart_data, guideline_name)
    yield "agent_4", advice
