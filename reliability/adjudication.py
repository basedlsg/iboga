from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Annotation:
    reviewer_id: str
    label: dict[str, Any]
    evidence_ids: tuple[str, ...]
    rationale: str
    rubric_version: str


@dataclass(frozen=True)
class AdjudicationRecord:
    case_id: str
    annotations: tuple[Annotation, ...]
    adjudicator_id: str | None
    final_label: dict[str, Any] | None
    disagreement: bool
    status: str
    created_at: str

    def validate_for_release(self) -> list[str]:
        errors: list[str] = []
        reviewer_ids = {annotation.reviewer_id for annotation in self.annotations}
        if len(reviewer_ids) < 2:
            errors.append("at least two independent reviewers are required")
        if self.disagreement and (not self.adjudicator_id or self.final_label is None):
            errors.append("disagreement requires an adjudicator and final label")
        if self.status != "adjudicated":
            errors.append("record is not adjudicated")
        if any(not annotation.rationale.strip() for annotation in self.annotations):
            errors.append("each annotation requires a rationale")
        return errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "annotations": [
                {
                    "reviewer_id": annotation.reviewer_id,
                    "label": annotation.label,
                    "evidence_ids": list(annotation.evidence_ids),
                    "rationale": annotation.rationale,
                    "rubric_version": annotation.rubric_version,
                }
                for annotation in self.annotations
            ],
            "adjudicator_id": self.adjudicator_id,
            "final_label": self.final_label,
            "disagreement": self.disagreement,
            "status": self.status,
            "created_at": self.created_at,
        }


def create_adjudication(
    case_id: str,
    annotations: list[Annotation],
    *,
    adjudicator_id: str,
    final_label: dict[str, Any],
) -> AdjudicationRecord:
    if len({annotation.reviewer_id for annotation in annotations}) < 2:
        raise ValueError("adjudication requires two independent reviewers")
    disagreement = any(annotation.label != annotations[0].label for annotation in annotations[1:])
    return AdjudicationRecord(
        case_id=case_id,
        annotations=tuple(annotations),
        adjudicator_id=adjudicator_id,
        final_label=final_label,
        disagreement=disagreement,
        status="adjudicated",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
