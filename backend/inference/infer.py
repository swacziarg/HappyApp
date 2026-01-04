
from inference.mood_rules import (
    clamp,
    sleep_contribution,
    cardio_contribution,
    stress_contribution,
    activity_contribution,
)
from inference.confidence import compute_confidence
from inference.explain import explain_feature, generate_explanations


BASELINE_MOOD = 3.0
MODEL_VERSION = "rules_v1"


def infer_mood(row):
    """
    Infer daily mood from physiological feature row.

    Returns a continuous mood score on [1.0, 5.0],
    plus confidence and human-readable explanations.
    """

    # --- Compute feature contributions ---
    sleep_delta = sleep_contribution(row)
    cardio_delta = cardio_contribution(row)
    stress_delta = stress_contribution(row)
    activity_delta = activity_contribution(row)

    # --- Aggregate score ---
    raw_score = (
        BASELINE_MOOD
        + sleep_delta
        + cardio_delta
        + stress_delta
        + activity_delta
    )

    # Continuous mood score (do NOT round here)
    mood_continuous = clamp(raw_score)

    # Optional discrete version (for UI, if needed later)
    mood_discrete = round(mood_continuous)

    # --- Build explanations ---
    explanations = generate_explanations([
        explain_feature(
            "sleep",
            row.get("sleep_debt_minutes"),
            sleep_delta,
            "Sleep relative to baseline"
        ),
        explain_feature(
            "cardio",
            row.get("hrv_rmssd_zscore"),
            cardio_delta,
            "Autonomic recovery indicators"
        ),
        explain_feature(
            "stress",
            row.get("stress_percentile"),
            stress_delta,
            "Stress level relative to baseline"
        ),
        explain_feature(
            "activity",
            row.get("steps_vs_baseline_pct"),
            activity_delta,
            "Activity relative to baseline"
        ),
    ])

    return {
        "predicted_mood": float(round(mood_continuous, 2)),
        "predicted_mood_discrete": int(mood_discrete),
        "confidence": compute_confidence(row),
        "explanation": explanations,
        "model_version": MODEL_VERSION,
    }
