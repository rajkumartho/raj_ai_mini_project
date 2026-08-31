
import json
from pydantic import BaseModel
from typing import List

from database import get_active_criteria


# ---------------------------------------------------------
# PYDANTIC MODELS
# ---------------------------------------------------------

class CriterionResult(BaseModel):

    criterion_id: int
    score: float
    max_score: float
    justification: str
    evidence: str


class SupplierEvaluation(BaseModel):

    supplier_name: str
    criteria: List[CriterionResult]
    risks: List[str]
    overall_summary: str


# ---------------------------------------------------------
# VALIDATE AND NORMALIZE
# ---------------------------------------------------------

def validate_and_normalize_evaluation(
    llm_response
):

    warnings = []

    # 1. Parse JSON
    try:

        data = json.loads(llm_response)

    except json.JSONDecodeError as e:

        raise ValueError(
            f"Invalid JSON from LLM: {e}"
        )

    # 2. Pydantic schema validation
    try:

        evaluation = (
            SupplierEvaluation
            .model_validate(data)
        )

    except Exception as e:

        raise ValueError(
            f"Schema validation failed: {e}"
        )

    # 3. Load active criteria
    active_criteria = get_active_criteria()

    expected_ids = {
        c["criterion_id"]: c
        for c in active_criteria
    }

    existing_ids = {
        c.criterion_id
        for c in evaluation.criteria
    }

    # 4. Missing criteria
    for criterion_id, criterion in expected_ids.items():

        if criterion_id not in existing_ids:

            warnings.append(
                f"Missing criterion: {criterion['name']}"
            )

            evaluation.criteria.append(
                CriterionResult(
                    criterion_id=criterion_id,
                    score=0,
                    max_score=criterion["max_score"],
                    justification=(
                        "No evaluation returned by LLM."
                    ),
                    evidence=(
                        "No evidence available."
                    )
                )
            )

    # 5. Normalize scores
    for criterion_result in evaluation.criteria:

        criterion_id = (
            criterion_result.criterion_id
        )

        if criterion_id not in expected_ids:

            warnings.append(
                f"Unexpected criterion ID: {criterion_id}"
            )

            continue

        expected_max = (
            expected_ids[criterion_id]["max_score"]
        )

        original_score = criterion_result.score

        normalized_score = max(
            0,
            min(
                original_score,
                expected_max
            )
        )

        if normalized_score != original_score:

            warnings.append(
                f"Criterion {criterion_id}: "
                f"score {original_score} normalized to "
                f"{normalized_score}"
            )

        criterion_result.score = normalized_score
        criterion_result.max_score = expected_max

    return evaluation, warnings
