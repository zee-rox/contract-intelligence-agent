from pathlib import Path

from eval.runner import compute_metrics, run_evaluation


def test_compute_metrics_uses_actual_predictions() -> None:
    metrics, errors = compute_metrics(
        [
            {
                "dataset_document_id": "doc",
                "expected_clauses": [{"clause_type": "termination", "snippet": "thirty days", "risk_level": "low"}],
                "predicted_clauses": [
                    {"clause_id": "clause_0000", "clause_type": "termination", "clause_text": "terminate with thirty days notice"}
                ],
                "chunks": [],
                "predicted_risks": [{"clause_id": "clause_0000", "risk_level": "low"}],
                "qa_results": [{"question": "q", "expected_refused": False, "response": {"refused": False, "citations": []}}],
                "ocr_expected_pages": 0,
                "ocr_actual_pages": 0,
            }
        ]
    )

    assert metrics["clause"]["precision"] == 1.0
    assert metrics["clause"]["recall"] == 1.0
    assert metrics["risk"]["accuracy"] == 1.0
    assert errors["weak_clause_categories"] == []


def test_run_evaluation_writes_json_and_markdown(tmp_path) -> None:
    eval_md = tmp_path / "EVAL.md"
    results = run_evaluation(output_dir=tmp_path / "results", eval_md_path=eval_md)

    assert Path(results["result_path"]).exists()
    assert eval_md.exists()
    assert results["dataset_version"] == "phase5-synthetic-v1"
    assert "Metrics" in eval_md.read_text(encoding="utf-8")
