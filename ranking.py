
from database import get_active_criteria


# ---------------------------------------------------------
# ABSOLUTE WEIGHTED SCORE
# ---------------------------------------------------------

def calculate_absolute_score(evaluation):

    active_criteria = get_active_criteria()

    criteria_lookup = {
        c["criterion_id"]: c
        for c in active_criteria
    }

    total_score = 0.0
    criterion_details = []

    for result in evaluation.criteria:

        criterion = criteria_lookup[
            result.criterion_id
        ]

        score = result.score
        max_score = criterion["max_score"]
        weight = criterion["weight"]

        contribution = (
            score / max_score
        ) * weight

        total_score += contribution

        criterion_details.append({
            "criterion_id": result.criterion_id,
            "criterion_name": criterion["name"],
            "score": score,
            "max_score": max_score,
            "weight": weight,
            "weighted_contribution": contribution,
            "justification": result.justification,
            "evidence": result.evidence
        })

    return total_score, criterion_details


# ---------------------------------------------------------
# PEER BENCHMARK
# ---------------------------------------------------------

def calculate_peer_benchmarks(
    supplier_results
):

    benchmarks = {}

    criterion_ids = set()

    for result in supplier_results.values():

        for criterion in result["evaluation"].criteria:

            criterion_ids.add(
                criterion.criterion_id
            )

    for criterion_id in criterion_ids:

        scores = []

        for result in supplier_results.values():

            for criterion in result["evaluation"].criteria:

                if (
                    criterion.criterion_id
                    == criterion_id
                ):

                    scores.append(
                        criterion.score
                    )

        if scores:

            benchmarks[criterion_id] = max(
                scores
            )

    return benchmarks


# ---------------------------------------------------------
# PEER METRICS
# ---------------------------------------------------------

def calculate_peer_metrics(
    supplier_results,
    benchmarks
):

    all_metrics = {}

    for supplier_name, result in (
        supplier_results.items()
    ):

        supplier_metrics = []

        for criterion in result["evaluation"].criteria:

            criterion_id = (
                criterion.criterion_id
            )

            score = criterion.score

            benchmark = benchmarks[
                criterion_id
            ]

            # Criterion gap
            gap = score - benchmark

            # Safe relative performance
            if benchmark == 0:

                if score == 0:
                    relative_percentage = 100.0
                else:
                    relative_percentage = 0.0

            else:

                relative_percentage = (
                    score / benchmark
                ) * 100

            supplier_metrics.append({
                "criterion_id": criterion_id,
                "score": score,
                "benchmark": benchmark,
                "gap": gap,
                "relative_percentage":
                    relative_percentage
            })

        all_metrics[
            supplier_name
        ] = supplier_metrics

    return all_metrics


# ---------------------------------------------------------
# PEER PERFORMANCE INDEX
# ---------------------------------------------------------

def calculate_ppi(
    supplier_name,
    peer_metrics
):

    active_criteria = get_active_criteria()

    weight_lookup = {
        c["criterion_id"]: c["weight"]
        for c in active_criteria
    }

    weighted_total = 0.0
    total_weight = 0.0

    for metric in peer_metrics[
        supplier_name
    ]:

        criterion_id = metric[
            "criterion_id"
        ]

        relative_percentage = metric[
            "relative_percentage"
        ]

        weight = weight_lookup[
            criterion_id
        ]

        weighted_total += (
            relative_percentage * weight
        )

        total_weight += weight

    if total_weight == 0:
        return 0.0

    return (
        weighted_total /
        total_weight
    )


# ---------------------------------------------------------
# ALL PPI RESULTS
# ---------------------------------------------------------

def calculate_all_ppi(
    supplier_results,
    peer_metrics
):

    ppi_results = {}

    for supplier_name in supplier_results:

        ppi_results[
            supplier_name
        ] = calculate_ppi(
            supplier_name,
            peer_metrics
        )

    return ppi_results


# ---------------------------------------------------------
# DETERMINISTIC RANKING
# ---------------------------------------------------------

def rank_suppliers(
    supplier_results,
    ppi_results,
    supplier_metadata
):

    ranking_data = []

    for supplier_name, result in (
        supplier_results.items()
    ):

        metadata = supplier_metadata[
            supplier_name
        ]

        ranking_data.append({

            "supplier_name":
                supplier_name,

            "absolute_score":
                result["absolute_score"],

            "ppi":
                ppi_results[supplier_name],

            "submission_date":
                metadata["submission_date"],

            "experience_rating":
                metadata[
                    "experience_rating"
                ]
        })

    # -----------------------------------------------------
    # REQUIRED TIE-BREAK ORDER
    #
    # 1. Higher PPI
    # 2. Earlier submission date
    # 3. Higher historical experience rating
    # 4. Supplier name ascending
    # -----------------------------------------------------

    ranking_data.sort(
        key=lambda x: (
            -x["ppi"],
            x["submission_date"],
            -x["experience_rating"],
            x["supplier_name"].lower()
        )
    )

    # Assign sequential ranks
    for rank, supplier in enumerate(
        ranking_data,
        start=1
    ):

        supplier[
            "final_rank"
        ] = rank

    return ranking_data
