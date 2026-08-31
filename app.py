
import streamlit as st
import os
import json
from datetime import datetime

from database import (
    get_active_criteria,
    create_rfp_run,
    save_supplier_result,
    complete_rfp_run
)

from pdf_utils import extract_pdf_text

from evaluation import evaluate_supplier

from validation import (
    validate_and_normalize_evaluation
)

from ranking import (
    calculate_absolute_score,
    calculate_peer_benchmarks,
    calculate_peer_metrics,
    calculate_all_ppi,
    rank_suppliers
)


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Agentic RFP Evaluation",
    page_icon="📊",
    layout="wide"
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "evaluation_results" not in st.session_state:
    st.session_state.evaluation_results = None

if "rfp_run_id" not in st.session_state:
    st.session_state.rfp_run_id = None

if "supplier_metadata" not in st.session_state:
    st.session_state.supplier_metadata = {}


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------

def generate_run_id():

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    return f"RUN-{timestamp}"


def build_complete_result(
    supplier_name,
    supplier_results,
    peer_metrics,
    final_ranking
):

    supplier_result = supplier_results[
        supplier_name
    ]

    ranking_info = next(
        item
        for item in final_ranking
        if item["supplier_name"] == supplier_name
    )

    complete_result = {

        "supplier_name":
            supplier_name,

        "absolute_score":
            supplier_result["absolute_score"],

        "ppi":
            ranking_info["ppi"],

        "final_rank":
            ranking_info["final_rank"],

        "submission_date":
            ranking_info["submission_date"],

        "experience_rating":
            ranking_info["experience_rating"],

        "criteria": [],

        "risks":
            supplier_result["evaluation"].risks,

        "warnings":
            supplier_result["warnings"],

        "overall_summary":
            supplier_result[
                "evaluation"
            ].overall_summary
    }

    for detail in supplier_result[
        "criterion_details"
    ]:

        metric = next(
            m
            for m in peer_metrics[
                supplier_name
            ]
            if m["criterion_id"]
            == detail["criterion_id"]
        )

        complete_result["criteria"].append({

            "criterion_id":
                detail["criterion_id"],

            "criterion_name":
                detail["criterion_name"],

            "score":
                detail["score"],

            "max_score":
                detail["max_score"],

            "weight":
                detail["weight"],

            "weighted_contribution":
                detail[
                    "weighted_contribution"
                ],

            "benchmark":
                metric["benchmark"],

            "gap":
                metric["gap"],

            "relative_percentage":
                metric[
                    "relative_percentage"
                ],

            "justification":
                detail["justification"],

            "evidence":
                detail["evidence"]
        })

    return complete_result


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.title(
    "📊 RFP Evaluation"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Criteria",
        "Supplier Evaluation",
        "Leaderboard",
        "Run Details"
    ]
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title(
    "🤖 Agentic RFP Evaluation"
)

st.caption(
    "AI-assisted supplier evaluation "
    "and deterministic ranking"
)


# =========================================================
# API KEY
# =========================================================

with st.sidebar:

    st.divider()

    st.subheader(
        "🔐 OpenRouter API"
    )

    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-v1-..."
    )

    st.caption(
        "Your API key is used only for "
        "the current Streamlit session."
    )

    if api_key:

        st.success(
            "✅ API key entered"
        )

    else:

        st.warning(
            "Enter an API key to evaluate suppliers."
        )


# =========================================================
# PAGE 1 — CRITERIA
# =========================================================

if page == "Criteria":

    st.header(
        "📋 Evaluation Criteria"
    )

    criteria = get_active_criteria()

    if not criteria:

        st.error(
            "No active evaluation criteria found."
        )

    else:

        total_weight = sum(
            c["weight"]
            for c in criteria
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Active Criteria",
                len(criteria)
            )

        with col2:

            st.metric(
                "Total Weight",
                f"{total_weight:.0f}%"
            )

        if abs(
            total_weight - 100.0
        ) < 0.001:

            st.success(
                "✅ Criteria weights total 100%"
            )

        else:

            st.error(
                "❌ Criteria weights do not total 100%"
            )

        for criterion in criteria:

            col1, col2, col3 = (
                st.columns([5, 2, 2])
            )

            with col1:

                st.subheader(
                    f"{criterion['criterion_id']}. "
                    f"{criterion['name']}"
                )

                st.write(
                    criterion["description"]
                )

            with col2:

                st.metric(
                    "Weight",
                    f"{criterion['weight']:.0f}%"
                )

            with col3:

                st.metric(
                    "Max Score",
                    f"{criterion['max_score']:g}"
                )

            st.divider()


# =========================================================
# PAGE 2 — SUPPLIER EVALUATION
# =========================================================

elif page == "Supplier Evaluation":

    st.header(
        "📄 Supplier Evaluation"
    )

    if not api_key:

        st.warning(
            "🔐 Please enter your OpenRouter API key "
            "in the sidebar before starting evaluation."
        )

    uploaded_files = st.file_uploader(
        "Upload Supplier RFP PDFs",
        type=["pdf"],
        accept_multiple_files=True
    )

    if not uploaded_files:

        st.info(
            "Please upload one or more supplier PDFs."
        )

    else:

        st.success(
            f"{len(uploaded_files)} supplier "
            f"PDF(s) uploaded."
        )

        supplier_metadata = {}

        for index, uploaded_file in enumerate(
            uploaded_files
        ):

            default_name = (
                os.path.splitext(
                    uploaded_file.name
                )[0]
                .replace("_", " ")
            )

            st.markdown(
                f"### Supplier {index + 1}"
            )

            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:

                supplier_name = st.text_input(
                    "Supplier Name",
                    value=default_name,
                    key=f"name_{index}"
                )

            with col2:

                submission_date = st.date_input(
                    "Submission Date",
                    key=f"date_{index}"
                )

            with col3:

                experience_rating = (
                    st.number_input(
                        "Historical Experience Rating",
                        min_value=0.0,
                        max_value=10.0,
                        value=5.0,
                        step=0.5,
                        key=f"experience_{index}"
                    )
                )

            supplier_metadata[
                supplier_name
            ] = {

                "submission_date":
                    str(submission_date),

                "experience_rating":
                    experience_rating,

                "filename":
                    uploaded_file.name,

                "file":
                    uploaded_file
            }

            st.divider()


        # -------------------------------------------------
        # EVALUATE BUTTON
        # -------------------------------------------------

        if st.button(
            "🚀 Evaluate Suppliers",
            type="primary",
            use_container_width=True
        ):

            if not api_key:

                st.error(
                    "Please enter your OpenRouter API key."
                )

                st.stop()


            if len(supplier_metadata) != len(
                uploaded_files
            ):

                st.error(
                    "Supplier names must be unique."
                )

                st.stop()


            # ---------------------------------------------
            # CREATE RUN
            # ---------------------------------------------

            rfp_run_id = generate_run_id()

            st.session_state.rfp_run_id = (
                rfp_run_id
            )

            create_rfp_run(
                rfp_run_id
            )

            supplier_results = {}

            progress = st.progress(0)

            status = st.empty()

            try:

                total_suppliers = len(
                    uploaded_files
                )

                # -----------------------------------------
                # EVALUATE SUPPLIERS
                # -----------------------------------------

                for index, uploaded_file in enumerate(
                    uploaded_files
                ):

                    supplier_name = (
                        os.path.splitext(
                            uploaded_file.name
                        )[0]
                        .replace("_", " ")
                    )

                    metadata = supplier_metadata[
                        supplier_name
                    ]

                    status.info(
                        f"Evaluating "
                        f"{supplier_name}..."
                    )

                    # -------------------------------------
                    # TEMP PDF
                    # -------------------------------------

                    temp_pdf = (
                        f"/tmp/"
                        f"{uploaded_file.name}"
                    )

                    with open(
                        temp_pdf,
                        "wb"
                    ) as f:

                        f.write(
                            uploaded_file.getbuffer()
                        )

                    # -------------------------------------
                    # EXTRACT PDF
                    # -------------------------------------

                    document_text = (
                        extract_pdf_text(
                            temp_pdf
                        )
                    )

                    # -------------------------------------
                    # LLM
                    # -------------------------------------

                    raw_result = (
                        evaluate_supplier(
                            supplier_name,
                            document_text,
                            api_key
                        )
                    )

                    # -------------------------------------
                    # VALIDATION
                    # -------------------------------------

                    validated_result, warnings = (
                        validate_and_normalize_evaluation(
                            raw_result
                        )
                    )

                    # -------------------------------------
                    # ABSOLUTE SCORE
                    # -------------------------------------

                    absolute_score, criterion_details = (
                        calculate_absolute_score(
                            validated_result
                        )
                    )

                    supplier_results[
                        supplier_name
                    ] = {

                        "supplier_name":
                            supplier_name,

                        "evaluation":
                            validated_result,

                        "absolute_score":
                            absolute_score,

                        "criterion_details":
                            criterion_details,

                        "warnings":
                            warnings
                    }

                    progress.progress(
                        (index + 1)
                        / total_suppliers
                    )

                # -----------------------------------------
                # PEER BENCHMARK
                # -----------------------------------------

                status.info(
                    "Calculating peer benchmarks..."
                )

                benchmarks = (
                    calculate_peer_benchmarks(
                        supplier_results
                    )
                )

                # -----------------------------------------
                # PEER METRICS
                # -----------------------------------------

                peer_metrics = (
                    calculate_peer_metrics(
                        supplier_results,
                        benchmarks
                    )
                )

                # -----------------------------------------
                # PPI
                # -----------------------------------------

                ppi_results = (
                    calculate_all_ppi(
                        supplier_results,
                        peer_metrics
                    )
                )

                # -----------------------------------------
                # RANKING METADATA
                # -----------------------------------------

                ranking_metadata = {}

                for supplier_name, metadata in (
                    supplier_metadata.items()
                ):

                    ranking_metadata[
                        supplier_name
                    ] = {

                        "submission_date":
                            metadata[
                                "submission_date"
                            ],

                        "experience_rating":
                            metadata[
                                "experience_rating"
                            ]
                    }

                # -----------------------------------------
                # FINAL RANKING
                # -----------------------------------------

                final_ranking = rank_suppliers(
                    supplier_results,
                    ppi_results,
                    ranking_metadata
                )

                # -----------------------------------------
                # COMPLETE RESULTS
                # -----------------------------------------

                complete_results = {}

                for supplier_name in (
                    supplier_results
                ):

                    complete_results[
                        supplier_name
                    ] = build_complete_result(
                        supplier_name,
                        supplier_results,
                        peer_metrics,
                        final_ranking
                    )

                # -----------------------------------------
                # SAVE SQLITE
                # -----------------------------------------

                for supplier_name, result in (
                    complete_results.items()
                ):

                    save_supplier_result(

                        rfp_run_id,

                        supplier_name,

                        result[
                            "submission_date"
                        ],

                        result[
                            "experience_rating"
                        ],

                        result[
                            "absolute_score"
                        ],

                        result[
                            "ppi"
                        ],

                        result[
                            "final_rank"
                        ],

                        json.dumps(
                            result
                        )
                    )

                complete_rfp_run(
                    rfp_run_id
                )

                # -----------------------------------------
                # SESSION STATE
                # -----------------------------------------

                st.session_state.evaluation_results = (
                    complete_results
                )

                st.session_state.supplier_metadata = (
                    ranking_metadata
                )

                status.success(
                    "✅ Evaluation completed successfully!"
                )

                st.balloons()

            except Exception as e:

                st.error(
                    f"❌ Evaluation failed: {e}"
                )

                st.exception(e)


# =========================================================
# PAGE 3 — LEADERBOARD
# =========================================================

elif page == "Leaderboard":

    st.header(
        "🏆 Supplier Leaderboard"
    )

    results = (
        st.session_state.evaluation_results
    )

    if not results:

        st.info(
            "No evaluation results available. "
            "Run a supplier evaluation first."
        )

    else:

        leaderboard = []

        for supplier_name, result in (
            results.items()
        ):

            leaderboard.append({

                "Rank":
                    result["final_rank"],

                "Supplier":
                    supplier_name,

                "Absolute Score":
                    round(
                        result["absolute_score"],
                        2
                    ),

                "PPI (%)":
                    round(
                        result["ppi"],
                        2
                    ),

                "Experience":
                    result[
                        "experience_rating"
                    ],

                "Submission Date":
                    result[
                        "submission_date"
                    ]
            })

        leaderboard.sort(
            key=lambda x: x["Rank"]
        )

        st.dataframe(
            leaderboard,
            use_container_width=True,
            hide_index=True
        )

        winner = leaderboard[0]

        st.success(
            f"🏆 Recommended Supplier: "
            f"**{winner['Supplier']}**"
        )


# =========================================================
# PAGE 4 — RUN DETAILS
# =========================================================

elif page == "Run Details":

    st.header(
        "🔎 Run Details"
    )

    run_id = (
        st.session_state.rfp_run_id
    )

    results = (
        st.session_state.evaluation_results
    )

    if not run_id:

        st.info(
            "No evaluation run available."
        )

    else:

        st.code(
            run_id,
            language=None
        )

        st.subheader(
            "Ranking Rules"
        )

        st.write(
            """
            1. Higher PPI
            2. Earlier submission date
            3. Higher historical experience rating
            4. Supplier name ascending
            """
        )

        if results:

            st.subheader(
                "Validation Status"
            )

            total_warnings = 0

            for supplier_name, result in (
                results.items()
            ):

                warnings = result[
                    "warnings"
                ]

                total_warnings += len(
                    warnings
                )

                if warnings:

                    with st.expander(
                        f"⚠️ {supplier_name}"
                    ):

                        for warning in warnings:

                            st.warning(
                                warning
                            )

                else:

                    st.success(
                        f"✅ {supplier_name}: "
                        f"No validation warnings"
                    )

            st.metric(
                "Total Validation Warnings",
                total_warnings
            )

            # ---------------------------------------------
            # JSON DOWNLOAD
            # ---------------------------------------------

            export_data = {

                "rfp_run_id":
                    run_id,

                "results":
                    list(
                        results.values()
                    )
            }

            json_data = json.dumps(
                export_data,
                indent=2
            )

            st.download_button(
                label="📥 Download Complete JSON",
                data=json_data,
                file_name=(
                    f"{run_id}.json"
                ),
                mime="application/json",
                use_container_width=True
            )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.sidebar.divider()

st.sidebar.caption(
    "Agentic RFP Evaluation System"
)

st.sidebar.caption(
    "AI evaluation + deterministic ranking"
)
