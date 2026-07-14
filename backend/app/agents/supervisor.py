import logging
from uuid import UUID

from langgraph.graph import END, StateGraph

from app.agents.clause_extraction import extract_clauses_single_pass
from app.agents.risk_assessment import assess_clause_risk
from app.agents.state import AnalysisState
from app.config import Settings
from app.schemas.analysis import AnalysisManifest, ClauseAnalysisResult
from app.schemas.chunks import CandidateChunk

logger = logging.getLogger(__name__)


class AnalysisSupervisor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        graph = StateGraph(AnalysisState)
        graph.add_node("extract_clauses", self._extract_node)
        graph.add_node("assess_risk", self._risk_node)
        graph.set_entry_point("extract_clauses")
        graph.add_edge("extract_clauses", "assess_risk")
        graph.add_edge("assess_risk", END)
        self.graph = graph.compile()

    def run(self, document_id: UUID, chunks: list[CandidateChunk]) -> ClauseAnalysisResult:
        state: AnalysisState = {
            "document_id": document_id,
            "warnings": [],
            "stage": "started",
            "chunks": chunks,
        }
        final_state = self.graph.invoke(state)
        clause_result = final_state["clause_result"]
        risks = final_state["risks"]
        warnings = list(clause_result.warnings) + list(final_state.get("warnings", []))
        manifest = AnalysisManifest(
            document_id=document_id,
            status="completed" if len(risks) == len(clause_result.clauses) else "partial_failure",
            prompt_version=self.settings.clause_prompt_version,
            risk_baseline_version=self.settings.risk_baseline_version,
            provider=clause_result.provider,
            model=clause_result.model,
            warnings=warnings,
        )
        return ClauseAnalysisResult(document_id=document_id, clauses=clause_result.clauses, risks=risks, manifest=manifest)

    def _extract_node(self, state: AnalysisState) -> AnalysisState:
        result = extract_clauses_single_pass(state["document_id"], state["chunks"], self.settings)
        logger.info("analysis extraction completed clauses=%s fallback=%s", len(result.clauses), result.fallback_used)
        return {"clause_result": result, "stage": "clauses_extracted"}

    def _risk_node(self, state: AnalysisState) -> AnalysisState:
        risks = []
        warnings = list(state.get("warnings", []))
        for clause in state["clause_result"].clauses:
            try:
                risks.append(assess_clause_risk(clause, self.settings.risk_baseline_version))
            except Exception as exc:  # pragma: no cover - defensive route for malformed future providers
                warnings.append(f"risk assessment failed for {clause.clause_id}: {exc}")
        logger.info("analysis risk assessment completed risks=%s", len(risks))
        return {"risks": risks, "warnings": warnings, "stage": "risks_assessed"}
