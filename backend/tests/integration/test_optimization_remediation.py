"""
Integration tests for Optimization Remediation Enhancement

Tests the complete remediation workflow including:
- Action tracking structure
- Status workflow
- COMPRESSION special handling
- Multiple actions persistence
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
    ImplementationEffort,
    EstimatedImpact,
    OptimizationAction,
    OptimizationActionType,
    OptimizationActionStatus,
)
from app.db.repositories.recommendation_repository import RecommendationRepository
from tests.fixtures.optimization_fixtures import (
    create_sample_recommendation,
    create_compression_recommendation,
)


@pytest.fixture
def recommendation_repo():
    """Recommendation repository fixture."""
    return RecommendationRepository()


class TestOptimizationRemediation:
    """Test optimization remediation workflows."""

    def test_compression_requires_manual_configuration(
        self, compression_recommendation, recommendation_repo
    ):
        """Test that COMPRESSION recommendations return manual configuration instructions."""
        # Get the recommendation
        rec = recommendation_repo.get_recommendation(str(compression_recommendation.id))
        assert rec is not None
        assert rec.recommendation_type == RecommendationType.COMPRESSION
        assert rec.status == RecommendationStatus.PENDING

        # Verify implementation steps are present
        assert len(rec.implementation_steps) > 0
        assert any("compression" in step.lower() for step in rec.implementation_steps)

    def test_action_tracking_structure(self):
        """Test that OptimizationAction has correct structure."""
        action = OptimizationAction(
            action="Test action",
            type=OptimizationActionType.APPLY_POLICY,
            status=OptimizationActionStatus.PENDING,
            performed_at=datetime.utcnow(),
            performed_by="test_user",
            gateway_policy_id="test_policy_123",
            error_message=None,
            metadata={"test_key": "test_value"},
        )

        # Verify all fields are present
        assert action.action == "Test action"
        assert action.type == OptimizationActionType.APPLY_POLICY
        assert action.status == OptimizationActionStatus.PENDING
        assert action.performed_by == "test_user"
        assert action.gateway_policy_id == "test_policy_123"
        assert action.metadata is not None
        assert action.metadata.get("test_key") == "test_value"

    def test_action_type_enum_values(self):
        """Test that OptimizationActionType enum has correct values."""
        assert OptimizationActionType.APPLY_POLICY == "apply_policy"
        assert OptimizationActionType.REMOVE_POLICY == "remove_policy"
        assert OptimizationActionType.VALIDATE == "validate"
        assert OptimizationActionType.MANUAL_CONFIGURATION == "manual_configuration"

    def test_action_status_enum_values(self):
        """Test that OptimizationActionStatus enum has correct values."""
        assert OptimizationActionStatus.COMPLETED == "completed"
        assert OptimizationActionStatus.PENDING == "pending"
        assert OptimizationActionStatus.FAILED == "failed"
        assert OptimizationActionStatus.IN_PROGRESS == "in_progress"

    def test_recommendation_has_remediation_actions_field(self, caching_recommendation):
        """Test that recommendations have remediation_actions field."""
        assert hasattr(caching_recommendation, "remediation_actions")
        assert isinstance(caching_recommendation.remediation_actions, list)

    def test_recommendation_status_workflow(self, caching_recommendation, recommendation_repo):
        """Test recommendation status transitions."""
        rec_id = str(caching_recommendation.id)

        # Initial status should be PENDING
        rec = recommendation_repo.get_recommendation(rec_id)
        assert rec.status == RecommendationStatus.PENDING

        # Update to IN_PROGRESS
        recommendation_repo.update(rec_id, {"status": RecommendationStatus.IN_PROGRESS.value})
        rec = recommendation_repo.get_recommendation(rec_id)
        assert rec.status == RecommendationStatus.IN_PROGRESS

        # Update to IMPLEMENTED
        recommendation_repo.update(
            rec_id,
            {
                "status": RecommendationStatus.IMPLEMENTED.value,
                "implemented_at": datetime.utcnow().isoformat(),
            },
        )
        rec = recommendation_repo.get_recommendation(rec_id)
        assert rec.status == RecommendationStatus.IMPLEMENTED
        assert rec.implemented_at is not None

    def test_action_history_persistence(self, recommendation_repo):
        """Test that actions are persisted correctly."""
        # Create a test recommendation
        test_rec = create_sample_recommendation()
        recommendation_repo.create_recommendation(test_rec)
        rec_id = str(test_rec.id)

        # Add an action
        action = OptimizationAction(
            action="Applied caching policy",
            type=OptimizationActionType.APPLY_POLICY,
            status=OptimizationActionStatus.COMPLETED,
            performed_at=datetime.utcnow(),
            performed_by="system",
            gateway_policy_id="policy_123",
            error_message=None,
            metadata={"policy_type": "caching"},
        )

        # Update recommendation with action
        recommendation_repo.update(
            rec_id, {"remediation_actions": [action.dict()]}
        )

        # Retrieve and verify
        rec = recommendation_repo.get_recommendation(rec_id)
        assert len(rec.remediation_actions) == 1
        assert rec.remediation_actions[0]["action"] == "Applied caching policy"
        assert rec.remediation_actions[0]["type"] == "apply_policy"
        assert rec.remediation_actions[0]["status"] == "completed"

    def test_multiple_actions_tracking(self, recommendation_repo):
        """Test tracking multiple actions on a recommendation."""
        # Create a test recommendation
        test_rec = create_sample_recommendation()
        recommendation_repo.create_recommendation(test_rec)
        rec_id = str(test_rec.id)

        # Add multiple actions
        actions = [
            OptimizationAction(
                action="Started applying policy",
                type=OptimizationActionType.APPLY_POLICY,
                status=OptimizationActionStatus.IN_PROGRESS,
                performed_at=datetime.utcnow(),
                performed_by="system",
                gateway_policy_id=None,
                error_message=None,
                metadata=None,
            ),
            OptimizationAction(
                action="Applied caching policy",
                type=OptimizationActionType.APPLY_POLICY,
                status=OptimizationActionStatus.COMPLETED,
                performed_at=datetime.utcnow(),
                performed_by="system",
                gateway_policy_id="policy_123",
                error_message=None,
                metadata=None,
            ),
            OptimizationAction(
                action="Validated impact",
                type=OptimizationActionType.VALIDATE,
                status=OptimizationActionStatus.COMPLETED,
                performed_at=datetime.utcnow(),
                performed_by="system",
                gateway_policy_id=None,
                error_message=None,
                metadata={"actual_improvement": 28.5},
            ),
        ]

        # Update recommendation with actions
        recommendation_repo.update(
            rec_id, {"remediation_actions": [a.dict() for a in actions]}
        )

        # Retrieve and verify
        rec = recommendation_repo.get_recommendation(rec_id)
        assert len(rec.remediation_actions) == 3
        assert rec.remediation_actions[0]["status"] == "in_progress"
        assert rec.remediation_actions[1]["status"] == "completed"
        assert rec.remediation_actions[2]["type"] == "validate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
