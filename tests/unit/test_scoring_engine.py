"""Unit tests for the scoring engine."""
import pytest
from unittest.mock import patch

from wecare.core.scoring.scoring_engine import ScoringEngine, ScoringError


class TestScoringEngine:
    """Test suite for the ScoringEngine."""

    def test_get_score_category(self):
        """Test the score category determination."""
        # Test each category boundary
        assert ScoringEngine.get_score_category(100) == "Excellent"
        assert ScoringEngine.get_score_category(81) == "Excellent"
        assert ScoringEngine.get_score_category(80) == "Good"
        assert ScoringEngine.get_score_category(61) == "Good"
        assert ScoringEngine.get_score_category(60) == "Average"
        assert ScoringEngine.get_score_category(41) == "Average"
        assert ScoringEngine.get_score_category(40) == "Low Quality"
        assert ScoringEngine.get_score_category(21) == "Low Quality"
        assert ScoringEngine.get_score_category(20) == "Very Low Quality"
        assert ScoringEngine.get_score_category(0) == "Very Low Quality"

    def test_get_score_category_invalid_value(self):
        """Test error handling for invalid score values."""
        with pytest.raises(ScoringError):
            ScoringEngine.get_score_category(101)
        
        with pytest.raises(ScoringError):
            ScoringEngine.get_score_category(-1)

    def test_calculate_score_missing_data(self):
        """Test error handling for missing product data."""
        with pytest.raises(ScoringError):
            ScoringEngine.calculate_score(None)  # type: ignore
        
        with pytest.raises(ScoringError):
            ScoringEngine.calculate_score({})

    def test_calculate_score_missing_nutrition(self):
        """Test error handling for missing nutrition data."""
        product_data = {
            "id": "123",
            "name": "Test Product",
            # No nutrition key
            "safe_additives": ["E100"],
            "suspicious_additives": ["E102"],
            "harmful_additives": ["E211"]
        }
        
        with pytest.raises(ScoringError) as excinfo:
            ScoringEngine.calculate_score(product_data)
        
        assert "Nutrition information is missing" in str(excinfo.value)

    def test_calculate_score_missing_additives_data(self):
        """Test error handling for missing additives data."""
        product_data = {
            "id": "123",
            "name": "Test Product",
            "nutrition": {
                "calories": 350,
                "protein": 8.5,
                "fat": {"total": 10.5, "saturated": 3.2},
                "carbohydrates": {"total": 45.0, "sugar": 12.5},
                "fiber": 2.5,
                "salt": 0.5,
                "sodium": 0.2
            }
            # Missing additives reference lists
        }
        
        with pytest.raises(ScoringError) as excinfo:
            ScoringEngine.calculate_score(product_data)
        
        assert "Both additives and ingredients information is missing" in str(excinfo.value)

    def test_calculate_nutrition_score(self):
        """Test nutrition score calculation."""
        product_data = {
            "nutrition": {
                "calories": 350,
                "protein": 8.5,  # High: 10 points
                "fat": {"total": 10.5, "saturated": 1.2},  # Low sat. fat: 10 points
                "carbohydrates": {"total": 45.0, "sugar": 4.5},  # Low sugar: 10 points
                "fiber": 6.5,  # High fiber: 10 points
                "salt": 0.2,  # Low salt: 10 points
                "sodium": 0.1
            }
        }
        
        # Expected weighted calculation:
        # (10 * 0.2) + (10 * 0.2) + (10 * 0.2) + (10 * 0.1) + (10 * 0.1) + (10 * 0.2) = 10
        # 10 * 10 = 100
        nutrition_score = ScoringEngine._calculate_nutrition_score(product_data)
        assert nutrition_score == 90

    def test_calculate_nutrition_score_medium_values(self):
        """Test nutrition score calculation with medium values."""
        product_data = {
            "nutrition": {
                "calories": 350,  # Medium: 5 points
                "protein": 3.0,  # Medium: 5 points
                "fat": {"total": 10.5, "saturated": 3.0},  # Medium sat. fat: 5 points
                "carbohydrates": {"total": 45.0, "sugar": 10.0},  # Medium sugar: 5 points
                "fiber": 3.5,  # Medium fiber: 5 points
                "salt": 1.0,  # Medium salt: 5 points
                "sodium": 0.4
            }
        }
        
        # Expected weighted calculation:
        # (5 * 0.2) + (5 * 0.2) + (5 * 0.2) + (5 * 0.1) + (5 * 0.1) + (5 * 0.2) = 5
        # 5 * 10 = 50
        nutrition_score = ScoringEngine._calculate_nutrition_score(product_data)
        assert nutrition_score == 50

    def test_calculate_nutrition_score_low_values(self):
        """Test nutrition score calculation with low values."""
        product_data = {
            "nutrition": {
                "calories": 450,  # High: 0 points
                "protein": 1.0,  # Low: 0 points
                "fat": {"total": 10.5, "saturated": 6.0},  # High sat. fat: 0 points
                "carbohydrates": {"total": 45.0, "sugar": 25.0},  # High sugar: 0 points
                "fiber": 1.5,  # Low fiber: 0 points
                "salt": 2.0,  # High salt: 0 points
                "sodium": 0.8
            }
        }
        
        # Expected weighted calculation:
        # (0 * 0.2) + (0 * 0.2) + (0 * 0.2) + (0 * 0.1) + (0 * 0.1) + (0 * 0.2) = 0
        # 0 * 10 = 0
        nutrition_score = ScoringEngine._calculate_nutrition_score(product_data)
        assert nutrition_score == 0

    def test_calculate_additives_score_all_safe(self):
        """Test additives score calculation with all safe additives."""
        product_data = {
            "additives": ["E300", "E306"],
            "ingredients": [],
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }
        
        # All additives are safe: 10 points
        # No suspicious additives: 10 points
        # No harmful additives: 10 points
        # (10 * 0.4) + (10 * 0.3) + (10 * 0.3) = 10
        # 10 * 10 = 100
        additives_score = ScoringEngine._calculate_additives_score(product_data)
        assert additives_score == 100

    def test_calculate_additives_score_mixed(self):
        """Test additives score calculation with mixed additives."""
        product_data = {
            "additives": ["E300", "E102"],  # One safe, one suspicious
            "ingredients": [],
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }
        
        # Some additives are safe: 5 points
        # Contains suspicious additives: 0 points
        # No harmful additives: 10 points
        # (5 * 0.4) + (0 * 0.3) + (10 * 0.3) = 5
        # 5 * 10 = 50
        additives_score = ScoringEngine._calculate_additives_score(product_data)
        assert additives_score == 50

    def test_calculate_additives_score_harmful(self):
        """Test additives score calculation with harmful additives."""
        product_data = {
            "additives": ["E300", "E211"],  # One safe, one harmful
            "ingredients": [],
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }
        
        # Some additives are safe: 5 points
        # No suspicious additives: 10 points
        # Contains harmful additives: 0 points
        # (5 * 0.4) + (10 * 0.3) + (0 * 0.3) = 5
        # 5 * 10 = 50
        additives_score = ScoringEngine._calculate_additives_score(product_data)
        assert additives_score == 50

    def test_calculate_additives_score_no_additives(self):
        """Test additives score calculation with no additives."""
        product_data = {
            "additives": [],
            "ingredients": [],
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }
        
        # No additives: 5 points (neutral)
        # No additives: 5 points (neutral)
        # No additives: 5 points (neutral)
        # (5 * 0.4) + (5 * 0.3) + (5 * 0.3) = 5
        # 5 * 10 = 50
        additives_score = ScoringEngine._calculate_additives_score(product_data)
        assert additives_score == 50

    def test_calculate_score_complete(self):
        """Test complete score calculation with all components."""
        product_data = {
            "id": "123",
            "name": "Test Product",
            "nutrition": {
                "calories": 350,  # Medium: 5 points
                "protein": 8.5,  # High: 10 points
                "fat": {"total": 10.5, "saturated": 1.2},  # Low sat. fat: 10 points
                "carbohydrates": {"total": 45.0, "sugar": 4.5},  # Low sugar: 10 points
                "fiber": 6.5,  # High fiber: 10 points
                "salt": 0.2,  # Low salt: 10 points
                "sodium": 0.1
            },
            "additives": ["E300", "E306"],  # All safe
            "ingredients": [],
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }
        
        # Nutrition score: (10 * 0.2) + (10 * 0.2) + (10 * 0.2) + (10 * 0.1) + (10 * 0.1) + (5 * 0.2) = 9 * 10 = 90
        # Additives score: (10 * 0.4) + (10 * 0.3) + (10 * 0.3) = 10 * 10 = 100
        # Total: (90 * 0.6) + (100 * 0.4) = 54 + 40 = 94 (Excellent)
        
        score = ScoringEngine.calculate_score(product_data)
        
        assert score.total == 94
        assert score.category == "Excellent"
        assert score.nutrition_score == 90
        assert score.additives_score == 100

    def test_calculate_score_poor_quality(self):
        """Test complete score calculation with poor quality product."""
        product_data = {
            "id": "123",
            "name": "Test Product",
            "nutrition": {
                "calories": 450,  # High: 0 points
                "protein": 1.0,  # Low: 0 points
                "fat": {"total": 10.5, "saturated": 6.0},  # High sat. fat: 0 points
                "carbohydrates": {"total": 45.0, "sugar": 25.0},  # High sugar: 0 points
                "fiber": 1.5,  # Low fiber: 0 points
                "salt": 2.0,  # High salt: 0 points
                "sodium": 0.8
            },
            "additives": ["E102", "E211"],  # One suspicious, one harmful
            "ingredients": [],
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }
        
        # Nutrition score: (0 * 0.2) + (0 * 0.2) + (0 * 0.2) + (0 * 0.1) + (0 * 0.1) + (0 * 0.2) = 0 * 10 = 0
        # Additives score: (0 * 0.4) + (0 * 0.3) + (0 * 0.3) = 0 * 10 = 0
        # Total: (0 * 0.6) + (0 * 0.4) = 0 (Very Low Quality)
        
        score = ScoringEngine.calculate_score(product_data)
        
        assert score.total == 0
        assert score.category == "Very Low Quality"
        assert score.nutrition_score == 0
        assert score.additives_score == 0

    def test_ingredient_additives_extraction(self):
        """Test extraction of additives from ingredients list."""
        product_data = {
            "additives": [],
            "ingredients": [
                {"name": "E300", "id": "en:e300"},
                {"name": "Sugar", "id": "en:sugar"},
                {"name": "E211", "id": "en:e211"}
            ],
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }
        
        # One safe, one harmful
        # Some additives are safe: 5 points
        # No suspicious additives: 10 points
        # Contains harmful additives: 0 points
        # (5 * 0.4) + (10 * 0.3) + (0 * 0.3) = 5
        # 5 * 10 = 50
        additives_score = ScoringEngine._calculate_additives_score(product_data)
        assert additives_score == 50

    def test_scoring_error_propagation(self):
        """Test that errors from component scores propagate to the main calculation."""
        product_data = {
            "id": "123",
            "name": "Test Product",
            "nutrition": {
                # Missing required nutrition fields
            },
            "additives": ["E300"],
            "ingredients": [],
            "safe_additives": ["E300"],
            "suspicious_additives": ["E102"],
            "harmful_additives": ["E211"]
        }
        
        with pytest.raises(ScoringError) as excinfo:
            ScoringEngine.calculate_score(product_data)
        
        assert "Failed to calculate nutrition score" in str(excinfo.value) 