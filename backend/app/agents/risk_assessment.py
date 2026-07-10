from app.schemas.clauses import ExtractedClause
from app.schemas.risks import RiskAssessment


def assess_clause_risk(clause: ExtractedClause, baseline_version: str) -> RiskAssessment:
    text = clause.clause_text.lower()
    observed: list[str] = []
    missing: list[str] = []
    risk_level = "low"

    if clause.clause_type == "liability":
        if "unlimited" in text:
            observed.append("The clause references unlimited liability.")
            risk_level = "high"
        if "cap" not in text and "limit" not in text:
            missing.append("No clear liability cap was detected.")
            if risk_level != "high":
                risk_level = "medium"
    elif clause.clause_type == "termination":
        if "notice" not in text:
            missing.append("No notice period was detected.")
            risk_level = "medium"
    elif clause.clause_type == "payment_terms":
        if "day" not in text and "due" not in text:
            missing.append("No clear payment deadline was detected.")
            risk_level = "medium"
    elif clause.clause_type == "confidentiality":
        if "survive" not in text and "term" not in text:
            missing.append("No clear survival period was detected.")
            risk_level = "medium"

    if not observed and not missing:
        observed.append("No obvious baseline concern was detected in this clause.")

    reason = (
        f"The {clause.clause_type.replace('_', ' ')} clause is rated {risk_level} based on the automated baseline. "
        "This is informational only and does not replace legal review."
    )
    return RiskAssessment(
        clause_id=clause.clause_id,
        risk_level=risk_level,  # type: ignore[arg-type]
        risk_reason=reason,
        observed_factors=observed,
        missing_expected_elements=missing,
        confidence="medium",
        baseline_version=baseline_version,
    )
