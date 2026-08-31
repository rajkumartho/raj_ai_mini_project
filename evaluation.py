
# import os
from openai import OpenAI

from database import get_active_criteria


# ---------------------------------------------------------
# OPENROUTER CLIENT
# ---------------------------------------------------------

def get_llm_client(api_key):

  #  api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError(
              "OPENROUTER_API_KEY environment variable is not set."
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )


# ---------------------------------------------------------
# BUILD EVALUATION PROMPT
# ---------------------------------------------------------

def build_evaluation_prompt(
    supplier_name,
    document_text,
    criteria
):

    criteria_text = ""

    for criterion in criteria:

        criteria_text += f"""
Criterion ID: {criterion['criterion_id']}
Name: {criterion['name']}
Description: {criterion['description']}
Weight: {criterion['weight']}%
Maximum Score: {criterion['max_score']}

"""

    prompt = f"""
You are an expert procurement proposal evaluator.

Evaluate the supplier proposal below against the ACTIVE
evaluation criteria.

SUPPLIER:
{supplier_name}

ACTIVE EVALUATION CRITERIA:
{criteria_text}

SUPPLIER PROPOSAL:
{document_text}

IMPORTANT RULES:

1. Use ONLY information present in the supplier proposal.
2. Do not invent facts or evidence.
3. Evaluate EVERY active criterion exactly once.
4. Give each criterion a score between 0 and its maximum score.
5. Provide a concise justification for every score.
6. Provide supporting evidence from the proposal.
7. If evidence is missing, explicitly say that evidence is missing.
8. Do NOT calculate the final weighted score.
9. Do NOT calculate PPI.
10. Do NOT rank suppliers.
11. Return JSON only.
12. Follow the exact JSON structure below.

REQUIRED JSON FORMAT:

{{
    "supplier_name": "{supplier_name}",
    "criteria": [
        {{
            "criterion_id": 1,
            "score": 0,
            "max_score": 10,
            "justification": "Reason for the score",
            "evidence": "Supporting evidence from the proposal"
        }}
    ],
    "risks": [
        "Risk or missing information"
    ],
    "overall_summary": "Short overall assessment"
}}
"""

    return prompt


# ---------------------------------------------------------
# EVALUATE ONE SUPPLIER
# ---------------------------------------------------------

def evaluate_supplier(
    supplier_name,
    document_text,
    api_key
):

    criteria = get_active_criteria()

    if not criteria:
        raise ValueError(
            "No active evaluation criteria found."
        )

    client = get_llm_client(api_key)

    prompt = build_evaluation_prompt(
        supplier_name,
        document_text,
        criteria
    )

    response = client.chat.completions.create(
        model="qwen/qwen3-30b-a3b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise procurement "
                    "evaluation assistant. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content
