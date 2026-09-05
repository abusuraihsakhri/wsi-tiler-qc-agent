"""
Security and edge case tests for Wsi Tiler Qc Agent.
Tests path traversal protection, PHI guard edge cases, and audit trail integrity.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import warnings
from agents.base import (
    PHIGuard,
    AuditTrail,
    SecurityException,
    assert_no_phi,
)
from cli import _resolve_safe_path


class TestPHIGuardEdgeCases:
    """Test PHI guard handles edge cases correctly."""

    def test_phi_guard_with_empty_string(self):
        """Empty strings should pass without error."""
        PHIGuard.assert_no_phi("")

    def test_phi_guard_with_none(self):
        """None should pass without error."""
        PHIGuard.assert_no_phi(None)

    def test_phi_guard_with_ssn_pattern(self):
        """SSN pattern should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_phi_guard_with_mrn_pattern(self):
        """MRN pattern should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-12345678")

    def test_phi_guard_with_phone_number(self):
        """Phone number pattern should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_phi_guard_with_email(self):
        """Email pattern should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_phi_guard_with_clean_text(self):
        """Clean text without PHI should pass."""
        PHIGuard.assert_no_phi("Specimen KEY-001 optimal for analysis")

    def test_phi_redaction(self):
        """PHI redact should replace sensitive data."""
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 is stable")
        assert "MRN" not in redacted or "REDACTED" in redacted

    def test_phi_redaction_preserves_context(self):
        """PHI redaction should preserve non-PHI context."""
        redacted = PHIGuard.redact_phi("Analysis complete for specimen KEY-001")
        assert "KEY-001" in redacted


class TestAuditTrailSecurity:
    """Test audit trail security features."""

    def test_audit_trail_with_custom_key(self):
        """Audit trail should work with custom key."""
        trail = AuditTrail(secret_key="test-key-for-testing-only")
        entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"detail": "value"})
        assert entry["current_hash"] != ""
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_audit_trail_generates_key_when_not_set(self):
        """Audit trail should generate secure key when AUDIT_SECRET_KEY not set."""
        # Remove env var if present
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                trail = AuditTrail()
                # Should have issued a warning about ephemeral key
                assert any("AUDIT_SECRET_KEY" in str(warning.message) for warning in w)
        finally:
            if original is not None:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_audit_trail_chain_integrity(self):
        """Audit trail chain should maintain integrity."""
        trail = AuditTrail(secret_key="chain-test-key")
        trail.log("actor1", "tier1", "EVENT_1", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT_2", {"data": "value2"})
        trail.log("actor3", "tier3", "EVENT_3", {"data": "value3"})
        assert trail.verify_integrity() is True

    def test_audit_trail_phi_blocked_in_details(self):
        """Audit trail should block PHI in details."""
        trail = AuditTrail(secret_key="phi-test-key")
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"note": "Patient MRN-12345678"})


class TestPathTraversalProtection:
    """Test path traversal protection in batch processing."""

    def test_safe_path_within_working_dir(self):
        """Paths within working directory should be allowed."""
        path = _resolve_safe_path("sample.csv", must_exist=True)
        assert path.exists()

    def test_safe_path_rejects_traversal(self):
        """Path traversal attempts should be rejected."""
        with pytest.raises(ValueError, match="outside the working directory"):
            _resolve_safe_path("../../../etc/passwd")

    def test_safe_path_rejects_absolute_outside(self):
        """Absolute paths outside working directory should be rejected."""
        with pytest.raises(ValueError, match="outside the working directory"):
            _resolve_safe_path("/etc/passwd")

    def test_safe_path_nonexistent_input_raises(self):
        """Non-existent input files should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            _resolve_safe_path("nonexistent_file.csv", must_exist=True)


class TestEnrichmentSuiteResults:
    """Test enrichment suite returns correct number of results."""

    def test_enrichment_suite_unique_keys(self):
        """Enrichment suite should return unique keys for each engine."""
        from enrichment import WsitilerqcagentEnrichmentSuite
        suite = WsitilerqcagentEnrichmentSuite()
        results = suite.execute_all(primary_val=0.5, secondary_val=0.2)
        # Should have exactly 6 unique engines
        assert len(results) == 6
        expected_keys = {
            "OverviewEngine",
            "Enrichment1DicomWsiMetadataExtractionScannerFingerprintingEngine",
            "ImplementationEngine",
            "Enrichment2MultiresolutionFocusQualityHeatmapEngine",
            "Enrichment3OtsuTissueMaskTissueFoldSegmentationEngine",
            "Enrichment4PenmarkingArtifactDetectionWithColorDeconvolutionEngine",
        }
        assert set(results.keys()) == expected_keys
