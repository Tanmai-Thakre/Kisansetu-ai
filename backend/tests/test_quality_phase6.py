"""
Phase 6 — Backend tests for Quality Grading Assistance Agent.

Tests:
  - Cotton grading (good, average)
  - Groundnut grading (good, average)
  - Valid parameters
  - Missing optional parameters
  - Invalid parameter ranges (validation)
  - Image upload validation
  - Image analysis fallback
  - Quality score calculation
  - Confidence calculation
  - Price-impact calculation
  - API endpoint response structure
  - Unauthorized / invalid farmer_id

Run with: python -m pytest tests/test_quality_phase6.py -v
(from backend/ directory)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# 1. Grading rules — unit tests (no DB, no HTTP)
# ══════════════════════════════════════════════════════════════════════════════

class TestCottonGrading:
    """Tests for grading_rules.grade_cotton()"""

    def setup_method(self):
        from app.agents.quality.grading_rules import grade_cotton, GRADE_EXCELLENT, GRADE_GOOD, GRADE_AVERAGE, GRADE_POOR
        self.grade_cotton = grade_cotton
        self.EXCELLENT = GRADE_EXCELLENT
        self.GOOD = GRADE_GOOD
        self.AVERAGE = GRADE_AVERAGE
        self.POOR = GRADE_POOR

    # ── Good quality cotton ────────────────────────────────────────────────────
    def test_good_quality_cotton(self):
        params = {
            "moisture":       7.5,    # excellent
            "staple_length":  31.0,   # excellent
            "micronaire":     4.0,    # excellent
            "foreign_matter": 0.8,    # excellent
            "color":          4.5,    # excellent
            "uniformity":     85.0,   # excellent
        }
        result = self.grade_cotton(params)
        assert result.grade in (self.EXCELLENT, self.GOOD), f"Expected EXCELLENT/GOOD, got {result.grade}"
        assert result.quality_score >= 70.0
        assert result.confidence == 100.0
        assert result.crop == "Cotton"

    # ── Average quality cotton ─────────────────────────────────────────────────
    def test_average_quality_cotton(self):
        params = {
            "moisture":       11.0,   # average
            "staple_length":  25.0,   # average
            "foreign_matter": 3.5,    # average
            "color":          3.0,    # average
        }
        result = self.grade_cotton(params)
        assert result.grade in (self.AVERAGE, self.POOR, self.GOOD), f"Grade: {result.grade}"
        assert result.quality_score < 80.0
        assert result.confidence < 100.0   # not all params supplied

    # ── Poor quality cotton ────────────────────────────────────────────────────
    def test_poor_quality_cotton(self):
        params = {
            "moisture":       15.0,   # poor
            "foreign_matter": 8.0,    # poor
            "color":          1.5,    # poor
            "uniformity":     72.0,   # poor
        }
        result = self.grade_cotton(params)
        assert result.grade in (self.POOR, self.AVERAGE)
        assert result.quality_score < 60.0

    # ── Missing optional parameters ───────────────────────────────────────────
    def test_missing_optional_parameters(self):
        params = {"moisture": 8.0}  # only moisture
        result = self.grade_cotton(params)
        assert result.grade is not None
        assert 0 <= result.quality_score <= 100
        assert result.confidence < 100.0
        # staple_length etc. should be not_available
        from app.agents.quality.grading_rules import RATING_NA
        assert result.parameters["staple_length"].rating == RATING_NA

    # ── All params missing → neutral ──────────────────────────────────────────
    def test_all_params_missing(self):
        result = self.grade_cotton({})
        assert result.quality_score == 50.0
        assert result.confidence == 0.0

    # ── Grade boundaries ──────────────────────────────────────────────────────
    def test_grade_excellent_boundary(self):
        from app.agents.quality.grading_rules import _score_to_grade
        assert _score_to_grade(85) == "EXCELLENT"
        assert _score_to_grade(79) == "GOOD"
        assert _score_to_grade(62) == "GOOD"
        assert _score_to_grade(61) == "AVERAGE"
        assert _score_to_grade(44) == "AVERAGE"
        assert _score_to_grade(43) == "POOR"

    # ── Suggestions generated for poor params ─────────────────────────────────
    def test_suggestions_for_poor_params(self):
        params = {"moisture": 15.0, "foreign_matter": 8.0}
        result = self.grade_cotton(params)
        assert len(result.suggestions) >= 1

    # ── Price impact ──────────────────────────────────────────────────────────
    def test_price_impact_excellent(self):
        from app.agents.quality.grading_rules import GRADE_PRICE_IMPACT
        lo, hi = GRADE_PRICE_IMPACT["EXCELLENT"]
        assert lo > 0 and hi > lo

    def test_price_impact_poor_negative(self):
        from app.agents.quality.grading_rules import GRADE_PRICE_IMPACT
        lo, hi = GRADE_PRICE_IMPACT["POOR"]
        assert lo < 0


class TestGroundnutGrading:
    """Tests for grading_rules.grade_groundnut()"""

    def setup_method(self):
        from app.agents.quality.grading_rules import grade_groundnut, GRADE_EXCELLENT, GRADE_GOOD, GRADE_AVERAGE, GRADE_POOR
        self.grade_groundnut = grade_groundnut
        self.EXCELLENT = GRADE_EXCELLENT
        self.GOOD = GRADE_GOOD
        self.AVERAGE = GRADE_AVERAGE
        self.POOR = GRADE_POOR

    # ── Good quality groundnut ─────────────────────────────────────────────────
    def test_good_quality_groundnut(self):
        params = {
            "moisture":          6.5,    # excellent
            "kernel_appearance": 4.5,    # excellent
            "damaged_kernels":   1.5,    # excellent
            "foreign_matter":    0.8,    # excellent
            "kernel_size":       4.0,    # excellent
            "color":             4.5,    # excellent
        }
        result = self.grade_groundnut(params)
        assert result.grade in (self.EXCELLENT, self.GOOD), f"Expected EXCELLENT/GOOD, got {result.grade}"
        assert result.quality_score >= 70.0
        assert result.confidence == 100.0

    # ── Average quality groundnut ──────────────────────────────────────────────
    def test_average_quality_groundnut(self):
        params = {
            "moisture":        10.5,   # average
            "damaged_kernels":  7.0,   # average
            "foreign_matter":   3.0,   # average
        }
        result = self.grade_groundnut(params)
        assert result.grade in (self.AVERAGE, self.GOOD, self.POOR)
        assert result.confidence < 100.0

    # ── Missing optional params ───────────────────────────────────────────────
    def test_missing_optional_params_groundnut(self):
        result = self.grade_groundnut({})
        assert result.quality_score == 50.0
        assert result.confidence == 0.0

    # ── Suggestions generated ─────────────────────────────────────────────────
    def test_suggestions_groundnut(self):
        params = {"moisture": 13.0, "damaged_kernels": 15.0}
        result = self.grade_groundnut(params)
        assert len(result.suggestions) >= 1

    # ── Confidence reflects supplied params ───────────────────────────────────
    def test_confidence_partial_params(self):
        # Supply only 3 of 6 params (total weight ~0.65)
        params = {"moisture": 7.0, "damaged_kernels": 2.0, "foreign_matter": 1.0}
        result = self.grade_groundnut(params)
        assert result.confidence > 0 and result.confidence < 100


class TestGradeCropDispatcher:
    """Tests for grading_rules.grade_crop() dispatcher."""

    def test_cotton_dispatched(self):
        from app.agents.quality.grading_rules import grade_crop
        r = grade_crop("cotton", {"moisture": 8.0})
        assert r.crop == "Cotton"

    def test_groundnut_dispatched(self):
        from app.agents.quality.grading_rules import grade_crop
        r = grade_crop("groundnut", {"moisture": 7.0})
        assert r.crop == "Groundnut"

    def test_unsupported_crop_raises(self):
        from app.agents.quality.grading_rules import grade_crop
        with pytest.raises(ValueError, match="Unsupported crop"):
            grade_crop("wheat", {})

    def test_case_insensitive(self):
        from app.agents.quality.grading_rules import grade_crop
        r = grade_crop("COTTON", {"moisture": 9.0})
        assert r.crop == "Cotton"


# ══════════════════════════════════════════════════════════════════════════════
# 2. Pydantic schema validation
# ══════════════════════════════════════════════════════════════════════════════

class TestCottonParamsSchema:
    """Validation of CottonParams."""

    def _make(self, **kw):
        from app.schemas.quality import CottonParams
        return CottonParams(**kw)

    def test_valid_params(self):
        p = self._make(moisture=8.0, staple_length=30.0)
        assert p.moisture == 8.0

    def test_invalid_moisture_too_high(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(moisture=35.0)  # > 30

    def test_invalid_moisture_negative(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(moisture=-1.0)

    def test_invalid_micronaire(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(micronaire=0.5)  # < 1.0

    def test_invalid_color_too_high(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(color=6.0)   # > 5

    def test_all_none_is_valid(self):
        p = self._make()
        d = p.to_params_dict()
        assert all(v is None for v in d.values())


class TestGroundnutParamsSchema:

    def _make(self, **kw):
        from app.schemas.quality import GroundnutParams
        return GroundnutParams(**kw)

    def test_valid(self):
        p = self._make(moisture=7.0, damaged_kernels=3.0)
        assert p.moisture == 7.0

    def test_invalid_damaged_kernels(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(damaged_kernels=60.0)  # > 50

    def test_invalid_moisture_too_high(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(moisture=25.0)  # > 20


class TestQualityAssessmentRequestSchema:

    def test_invalid_crop(self):
        from pydantic import ValidationError
        from app.schemas.quality import QualityAssessmentRequest
        with pytest.raises(ValidationError):
            QualityAssessmentRequest(farmer_id=1, crop="wheat")

    def test_invalid_farmer_id(self):
        from pydantic import ValidationError
        from app.schemas.quality import QualityAssessmentRequest
        with pytest.raises(ValidationError):
            QualityAssessmentRequest(farmer_id=-1, crop="cotton")

    def test_cross_param_validation(self):
        """groundnut_params for crop=cotton should fail."""
        from pydantic import ValidationError
        from app.schemas.quality import QualityAssessmentRequest, GroundnutParams
        with pytest.raises(ValidationError):
            QualityAssessmentRequest(
                farmer_id=1,
                crop="cotton",
                groundnut_params=GroundnutParams(moisture=7.0),
            )

    def test_get_manual_params_cotton(self):
        from app.schemas.quality import QualityAssessmentRequest, CottonParams
        req = QualityAssessmentRequest(
            farmer_id=1,
            crop="cotton",
            cotton_params=CottonParams(moisture=8.0, foreign_matter=1.5),
        )
        params = req.get_manual_params()
        assert params["moisture"] == 8.0
        assert params["foreign_matter"] == 1.5
        assert params["staple_length"] is None

    def test_get_manual_params_empty(self):
        from app.schemas.quality import QualityAssessmentRequest
        req = QualityAssessmentRequest(farmer_id=1, crop="groundnut")
        assert req.get_manual_params() == {}


# ══════════════════════════════════════════════════════════════════════════════
# 3. Image analysis
# ══════════════════════════════════════════════════════════════════════════════

class TestImageAnalysis:

    def test_analyze_no_pillow_fallback(self):
        """Image analysis should fail gracefully if bytes are invalid."""
        from app.agents.quality.image_analysis import analyze_image
        obs = analyze_image(b"not-an-image", "cotton")
        # Should not crash; available should be False
        assert obs.available is False
        assert obs.error is not None

    def test_analyze_empty_bytes(self):
        from app.agents.quality.image_analysis import analyze_image
        obs = analyze_image(b"", "cotton")
        assert obs.available is False

    def test_not_detectable_cotton(self):
        """Cotton image analysis must list lab params as not detectable."""
        from app.agents.quality.image_analysis import _COTTON_NOT_DETECTABLE
        # These critical attributes must be in the not-detectable list
        combined = " ".join(_COTTON_NOT_DETECTABLE).lower()
        assert "moisture" in combined
        assert "micronaire" in combined or "staple" in combined

    def test_not_detectable_groundnut(self):
        from app.agents.quality.image_analysis import _GROUNDNUT_NOT_DETECTABLE
        combined = " ".join(_GROUNDNUT_NOT_DETECTABLE).lower()
        assert "moisture" in combined

    def test_merge_image_params_manual_takes_precedence(self):
        """Manual params should override image-derived estimates."""
        from app.agents.quality.image_analysis import merge_image_params, ImageObservation
        obs = ImageObservation(available=True, color_score=3.0)
        manual = {"color": 4.5}  # user provided
        merged, _ = merge_image_params(manual, obs, "cotton")
        assert merged["color"] == 4.5   # manual wins, not 3.0

    def test_merge_image_params_fills_missing(self):
        """Image estimate should fill params not provided by user."""
        from app.agents.quality.image_analysis import merge_image_params, ImageObservation
        obs = ImageObservation(available=True, color_score=3.8)
        manual = {"moisture": 8.0}  # color not provided
        merged, annotations = merge_image_params(manual, obs, "cotton")
        assert merged["color"] == 3.8
        assert any("color" in a for a in annotations)

    def test_merge_image_unavailable_no_changes(self):
        """When image is unavailable, manual params must not be altered."""
        from app.agents.quality.image_analysis import merge_image_params, ImageObservation
        obs = ImageObservation(available=False)
        manual = {"moisture": 9.0, "color": None}
        merged, annotations = merge_image_params(manual, obs, "cotton")
        assert merged == manual
        assert annotations == []


# ══════════════════════════════════════════════════════════════════════════════
# 4. QualityService integration (in-memory SQLite)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def test_db():
    """In-memory SQLite session for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database.base import Base
    from app.models import QualityAssessment  # ensures table is registered

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    yield db
    db.close()


class TestQualityService:

    def test_cotton_assessment_saves_and_returns(self, test_db):
        from app.agents.quality.quality_service import QualityService
        svc = QualityService()
        result = svc.assess(
            db=test_db,
            farmer_id=1,
            crop="cotton",
            manual_params={
                "moisture": 7.5,
                "foreign_matter": 1.0,
                "color": 4.5,
            },
        )
        assert result["crop"] == "Cotton"
        assert result["grade"] in ("EXCELLENT", "GOOD", "AVERAGE", "POOR")
        assert 0 <= result["quality_score"] <= 100
        assert 0 <= result["confidence"] <= 100
        assert "factors" in result
        assert "moisture" in result["factors"]
        assert "disclaimer" in result
        assert result["id"] >= 1

    def test_groundnut_assessment(self, test_db):
        from app.agents.quality.quality_service import QualityService
        svc = QualityService()
        result = svc.assess(
            db=test_db,
            farmer_id=2,
            crop="groundnut",
            manual_params={
                "moisture": 8.0,
                "damaged_kernels": 3.0,
            },
        )
        assert result["crop"] == "Groundnut"
        assert result["grade"] is not None

    def test_missing_image_no_crash(self, test_db):
        from app.agents.quality.quality_service import QualityService
        svc = QualityService()
        result = svc.assess(
            db=test_db,
            farmer_id=3,
            crop="cotton",
            manual_params={"moisture": 9.0},
            image_bytes=None,
        )
        assert result["image_used"] is False

    def test_invalid_image_bytes_graceful(self, test_db):
        from app.agents.quality.quality_service import QualityService
        svc = QualityService()
        result = svc.assess(
            db=test_db,
            farmer_id=4,
            crop="cotton",
            manual_params={"moisture": 9.0},
            image_bytes=b"garbage",
        )
        # Should not crash; limitations should mention image failure
        assert result["image_used"] is False
        assert len(result["limitations"]) >= 1

    def test_price_impact_present(self, test_db):
        from app.agents.quality.quality_service import QualityService
        svc = QualityService()
        result = svc.assess(
            db=test_db,
            farmer_id=5,
            crop="cotton",
            manual_params={"moisture": 7.5, "foreign_matter": 0.8, "color": 4.5},
        )
        assert result.get("reference_price") is not None
        assert result.get("estimated_quality_price") is not None
        assert result["price_impact_percent"] != 0  # should have a non-zero impact

    def test_history_returns_saved_assessments(self, test_db):
        from app.agents.quality.quality_service import QualityService
        svc = QualityService()
        farmer_id = 99
        # Save two assessments
        svc.assess(db=test_db, farmer_id=farmer_id, crop="cotton",
                   manual_params={"moisture": 8.0})
        svc.assess(db=test_db, farmer_id=farmer_id, crop="groundnut",
                   manual_params={"moisture": 7.0})
        history = svc.get_history(db=test_db, farmer_id=farmer_id)
        assert len(history) == 2
        crops = {h["crop"] for h in history}
        assert crops == {"cotton", "groundnut"}

    def test_history_empty_for_unknown_farmer(self, test_db):
        from app.agents.quality.quality_service import QualityService
        svc = QualityService()
        history = svc.get_history(db=test_db, farmer_id=99999)
        assert history == []

    def test_disclaimer_always_present(self, test_db):
        from app.agents.quality.quality_service import QualityService, DISCLAIMER
        svc = QualityService()
        result = svc.assess(db=test_db, farmer_id=10, crop="cotton", manual_params={})
        assert result["disclaimer"] == DISCLAIMER


# ══════════════════════════════════════════════════════════════════════════════
# 5. API endpoint tests (no live server — tests request validation)
# ══════════════════════════════════════════════════════════════════════════════

class TestAPIPreviewEndpoint:
    """Tests for /api/agents/quality/preview (no DB needed)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from fastapi.testclient import TestClient
        from main import app
        self.client = TestClient(app)

    def test_preview_cotton_good(self):
        resp = self.client.get(
            "/api/agents/quality/preview",
            params={"crop": "cotton", "moisture": 7.5, "foreign_matter": 1.0, "color": 4.5}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["grade"] in ("EXCELLENT", "GOOD", "AVERAGE", "POOR")
        assert "disclaimer" in data
        assert "quality_score" in data

    def test_preview_groundnut(self):
        resp = self.client.get(
            "/api/agents/quality/preview",
            params={"crop": "groundnut", "moisture": 8.0, "damaged_kernels": 3.0}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["grade"] is not None

    def test_preview_invalid_crop(self):
        resp = self.client.get("/api/agents/quality/preview", params={"crop": "wheat"})
        assert resp.status_code == 400

    def test_preview_no_params(self):
        resp = self.client.get("/api/agents/quality/preview", params={"crop": "cotton"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["quality_score"] == 50.0  # all params missing → neutral

    def test_preview_response_has_disclaimer(self):
        resp = self.client.get("/api/agents/quality/preview", params={"crop": "cotton"})
        assert "disclaimer" in resp.json()
        assert "Preliminary" in resp.json()["disclaimer"]


class TestAPIQualityJSONEndpoint:
    """Tests for POST /api/agents/quality (JSON body)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from fastapi.testclient import TestClient
        from main import app
        self.client = TestClient(app)

    def test_cotton_good_quality(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "cotton",
            "cotton_params": {
                "moisture": 7.5,
                "foreign_matter": 1.0,
                "color": 4.5,
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop"] == "Cotton"
        assert data["grade"] in ("EXCELLENT", "GOOD")
        assert "factors" in data
        assert "disclaimer" in data
        assert "image_used" in data

    def test_cotton_average_quality(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "cotton",
            "cotton_params": {
                "moisture": 11.5,
                "foreign_matter": 3.5,
                "color": 2.5,
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["grade"] in ("AVERAGE", "POOR", "GOOD")

    def test_groundnut_good_quality(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 2,
            "crop": "groundnut",
            "groundnut_params": {
                "moisture": 6.5,
                "kernel_appearance": 4.5,
                "damaged_kernels": 1.5,
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop"] == "Groundnut"
        assert data["grade"] in ("EXCELLENT", "GOOD", "AVERAGE")

    def test_missing_optional_parameters(self):
        """Assessment should work even with no quality params."""
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "cotton",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["quality_score"] == 50.0   # neutral when no params
        assert data["confidence"] == 0.0

    def test_invalid_crop(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "wheat",
        })
        assert resp.status_code == 422

    def test_invalid_farmer_id(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 0,
            "crop": "cotton",
        })
        assert resp.status_code == 422

    def test_invalid_parameter_values(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "cotton",
            "cotton_params": {"moisture": 50.0},  # > 30
        })
        assert resp.status_code == 422

    def test_unauthorized_cross_params(self):
        """groundnut_params for crop=cotton should fail validation."""
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "cotton",
            "groundnut_params": {"moisture": 7.0},
        })
        assert resp.status_code == 422

    def test_price_impact_in_response(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "cotton",
            "cotton_params": {"moisture": 7.5, "foreign_matter": 0.8, "color": 4.5},
        })
        data = resp.json()
        assert "price_impact_percent" in data
        assert "reference_price" in data
        assert data["reference_price"] is not None

    def test_response_structure(self):
        resp = self.client.post("/api/agents/quality", json={
            "farmer_id": 1,
            "crop": "cotton",
            "cotton_params": {"moisture": 9.0},
        })
        data = resp.json()
        required_keys = [
            "id", "crop", "grade", "quality_score", "confidence",
            "factors", "observations", "suggestions", "limitations",
            "image_used", "disclaimer", "source_status",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"


class TestAPIHistoryEndpoint:

    @pytest.fixture(autouse=True)
    def setup(self):
        from fastapi.testclient import TestClient
        from main import app
        self.client = TestClient(app)

    def test_history_invalid_farmer_id(self):
        resp = self.client.get("/api/agents/quality/history", params={"farmer_id": 0})
        assert resp.status_code == 400

    def test_history_returns_list(self):
        resp = self.client.get("/api/agents/quality/history", params={"farmer_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "count" in data
        assert isinstance(data["items"], list)
