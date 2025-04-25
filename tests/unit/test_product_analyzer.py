"""Unit tests for the product analyzer."""
import json
import pytest
from unittest.mock import MagicMock, patch, Mock

from wecare.services.ai_service.product_analyzer import ProductAnalyzer
from wecare.services.ai_service.gpt_client import GPTClient
from wecare.core.models.schemas import (
    AIServiceOutput, AllergenAnalysis, DietCompatibility, Score, 
    Weight, NutritionInfo, FatInfo, CarbInfo, ProductInfo, ProductAnalysis
)


class TestProductAnalyzer:
    """Test suite for the ProductAnalyzer."""

    @pytest.fixture
    def mock_gpt_client(self):
        """Fixture providing a mock GPT client."""
        mock_client = MagicMock(spec=GPTClient)
        
        # Set up a sample response
        mock_response = AIServiceOutput(
            allergens_analysis=AllergenAnalysis(
                detected_allergens=["Peanuts", "Soybeans"],
                user_allergens_present=["Peanuts"]
            ),
            diet_compatibility=[
                DietCompatibility(
                    diet="Vegetarian",
                    compatible=True,
                    reason="Contains no meat or animal products"
                ),
                DietCompatibility(
                    diet="Low-Sugar",
                    compatible=False,
                    reason="Contains more than 5g of sugar per 100g"
                )
            ],
            score=Score(
                total=75,
                category="Good",
                nutrition_score=80,
                additives_score=70
            )
        )
        
        mock_client.analyze_product.return_value = mock_response
        return mock_client

    @pytest.fixture
    def sample_product_data(self):
        """Fixture providing sample product data."""
        return {
            "id": "0737628064502",
            "product": {
                "_id": "0737628064502",
                "code": "0737628064502",
                "product_name": "Thai peanut noodle kit",
                "brand_owner": "Simply Asia Foods, Inc.",
                "quantity": "155 g",
                "ingredients": [
                    {"id": "en:rice", "text": "rice", "percent_estimate": 40},
                    {"id": "en:water", "text": "water", "percent_estimate": 30},
                    {"id": "en:peanut", "text": "peanut", "percent_estimate": 10},
                    {"id": "en:sugar", "text": "sugar", "percent_estimate": 5},
                    {"id": "en:e330", "text": "citric acid", "percent_estimate": 1},
                ],
                "additives_tags": ["en:e330"],
                "nutriments": {
                    "energy-kcal_100g": 385,
                    "proteins_100g": 9.62,
                    "fat_100g": 7.69,
                    "saturated-fat_100g": 1.92,
                    "carbohydrates_100g": 71.15,
                    "sugars_100g": 13.46,
                    "fiber_100g": 1.9,
                    "salt_100g": 0.72,
                    "sodium_100g": 0.288
                },
                "image_front_url": "https://example.com/image.jpg"
            },
            "safe_additives": ["E300", "E306", "E330"],
            "suspicious_additives": ["E102", "E104"],
            "harmful_additives": ["E211", "E250"]
        }

    def test_initialization(self):
        """Test ProductAnalyzer initialization."""
        analyzer = ProductAnalyzer(api_key="test_key")
        assert isinstance(analyzer.gpt_client, GPTClient)
        
        # Test with custom parameters
        analyzer = ProductAnalyzer(
            api_key="test_key",
            model="custom-model",
            guided_json={"custom": "template"}
        )
        assert isinstance(analyzer.gpt_client, GPTClient)

    @patch("wecare.services.ai_service.product_analyzer.GPTClient")
    def test_analyze_product_with_ai_scoring(self, mock_gpt_client_class, sample_product_data, mock_gpt_client):
        """Test product analysis with AI scoring."""
        # Set up the mock GPT client
        mock_gpt_client_class.return_value = mock_gpt_client
        
        # Create analyzer and analyze product
        analyzer = ProductAnalyzer(api_key="test_key")
        result = analyzer.analyze_product(
            product_info=sample_product_data,
            user_allergens=["Peanuts"],
            user_diets=["Vegetarian", "Low-Sugar"],
            use_ai_scoring=True
        )
        
        # Verify that GPT client was called with correct parameters
        mock_gpt_client.analyze_product.assert_called_once()
        call_args = mock_gpt_client.analyze_product.call_args[0][0]
        assert call_args.product_info == sample_product_data
        assert call_args.user_allergens == ["Peanuts"]
        assert call_args.user_diets == ["Vegetarian", "Low-Sugar"]
        assert call_args.calculate_score is True
        
        # Verify the result structure
        assert isinstance(result, ProductAnalysis)
        assert result.product.name == "Thai peanut noodle kit"
        assert result.allergens_analysis.detected_allergens == ["Peanuts", "Soybeans"]
        assert result.allergens_analysis.user_allergens_present == ["Peanuts"]
        assert len(result.diet_compatibility) == 2
        assert result.diet_compatibility[0].diet == "Vegetarian"
        assert result.diet_compatibility[0].compatible is True
        assert result.diet_compatibility[1].diet == "Low-Sugar"
        assert result.diet_compatibility[1].compatible is False
        assert result.product.score is not None
        assert result.product.score.total == 75
        assert result.product.score.category == "Good"

    @patch("wecare.services.ai_service.product_analyzer.GPTClient")
    def test_analyze_product_with_local_scoring(self, mock_gpt_client_class, sample_product_data, mock_gpt_client):
        """Test product analysis with local scoring engine."""
        # Set up the mock GPT client
        mock_gpt_client_class.return_value = mock_gpt_client
        
        # Create analyzer and analyze product with local scoring
        analyzer = ProductAnalyzer(api_key="test_key")
        
        with patch("wecare.services.ai_service.product_analyzer.ScoringEngine") as mock_scoring_engine:
            # Configure the mock scoring engine
            mock_score = Score(
                total=65,
                category="Good",
                nutrition_score=70,
                additives_score=60
            )
            mock_scoring_engine.calculate_score.return_value = mock_score
            
            # Analyze the product with local scoring
            result = analyzer.analyze_product(
                product_info=sample_product_data,
                user_allergens=["Peanuts"],
                user_diets=["Vegetarian", "Low-Sugar"],
                use_ai_scoring=False
            )
            
            # Verify that GPT client was called with correct parameters
            mock_gpt_client.analyze_product.assert_called_once()
            call_args = mock_gpt_client.analyze_product.call_args[0][0]
            assert call_args.product_info == sample_product_data
            assert call_args.user_allergens == ["Peanuts"]
            assert call_args.user_diets == ["Vegetarian", "Low-Sugar"]
            assert call_args.calculate_score is False
            
            # Verify that scoring engine was called
            mock_scoring_engine.calculate_score.assert_called_once_with(sample_product_data)
            
            # Verify the result structure
            assert isinstance(result, ProductAnalysis)
            assert result.product.score is not None
            assert result.product.score.total == 65
            assert result.product.score.category == "Good"

    @patch("wecare.services.ai_service.product_analyzer.GPTClient")
    def test_analyze_product_with_external_score(self, mock_gpt_client_class, sample_product_data, mock_gpt_client):
        """Test product analysis with external score."""
        # Set up the mock GPT client
        mock_gpt_client_class.return_value = mock_gpt_client
        
        # Add a score to the product data
        sample_product_data["score"] = {
            "total": 90,
            "category": "Excellent",
            "nutrition_score": 95,
            "additives_score": 85
        }
        
        # Create analyzer and analyze product
        analyzer = ProductAnalyzer(api_key="test_key")
        result = analyzer.analyze_product(
            product_info=sample_product_data,
            user_allergens=["Peanuts"],
            user_diets=["Vegetarian", "Low-Sugar"],
            use_ai_scoring=True  # This should be ignored since external score is available
        )
        
        # Verify that GPT client was called with correct parameters
        mock_gpt_client.analyze_product.assert_called_once()
        call_args = mock_gpt_client.analyze_product.call_args[0][0]
        assert call_args.calculate_score is False  # Should not request score calculation
        
        # Verify the result structure and external score usage
        assert isinstance(result, ProductAnalysis)
        assert result.product.score is not None
        assert result.product.score.total == 90
        assert result.product.score.category == "Excellent"

    @patch("wecare.services.ai_service.product_analyzer.GPTClient")
    def test_analyze_product_with_gpt_error(self, mock_gpt_client_class, sample_product_data):
        """Test product analysis with GPT error."""
        # Set up the mock GPT client to raise an exception
        mock_client = MagicMock(spec=GPTClient)
        mock_client.analyze_product.side_effect = Exception("API Error")
        mock_gpt_client_class.return_value = mock_client
        
        # Create analyzer and analyze product
        analyzer = ProductAnalyzer(api_key="test_key")
        
        with patch("wecare.services.ai_service.product_analyzer.ScoringEngine") as mock_scoring_engine:
            # Configure the mock scoring engine
            mock_score = Score(
                total=65,
                category="Good",
                nutrition_score=70,
                additives_score=60
            )
            mock_scoring_engine.calculate_score.return_value = mock_score
            
            # Analyze the product
            result = analyzer.analyze_product(
                product_info=sample_product_data,
                user_allergens=["Peanuts"],
                user_diets=["Vegetarian", "Low-Sugar"],
                use_ai_scoring=True
            )
            
            # Verify that fallback analysis was used
            assert isinstance(result, ProductAnalysis)
            assert result.allergens_analysis.detected_allergens == []
            assert result.allergens_analysis.user_allergens_present == []
            assert len(result.diet_compatibility) == 2
            assert result.diet_compatibility[0].diet == "Vegetarian"
            assert result.diet_compatibility[0].compatible is False
            assert "Unable to determine" in result.diet_compatibility[0].reason
            
            # Verify that local scoring was used
            assert isinstance(result, ProductAnalysis)
            assert result.product.score is not None
            assert result.product.score.total == 65
            assert result.product.score.category == "Good"

    def test_create_product_info(self, sample_product_data):
        """Test product info creation from raw data."""
        analyzer = ProductAnalyzer(api_key="test_key")
        
        score = Score(
            total=75,
            category="Good",
            nutrition_score=80,
            additives_score=70
        )
        
        # Create product info
        product_info = analyzer._create_product_info(sample_product_data, score)
        
        # Verify basic information
        assert isinstance(product_info, ProductInfo)
        assert product_info.id == "0737628064502"
        assert product_info.barcode == "0737628064502"
        assert product_info.name == "Thai peanut noodle kit"
        assert product_info.manufacturer == "Simply Asia Foods, Inc."
        
        # Verify weight parsing
        assert isinstance(product_info.weight, Weight)
        assert product_info.weight.value == 155.0
        assert product_info.weight.unit == "g"
        
        # Verify nutrition info
        assert isinstance(product_info.nutrition, NutritionInfo)
        assert product_info.nutrition.calories == 385
        assert product_info.nutrition.protein == 9.62
        assert isinstance(product_info.nutrition.fat, FatInfo)
        assert product_info.nutrition.fat.total == 7.69
        assert product_info.nutrition.fat.saturated == 1.92
        assert isinstance(product_info.nutrition.carbohydrates, CarbInfo)
        assert product_info.nutrition.carbohydrates.total == 71.15
        assert product_info.nutrition.carbohydrates.sugar == 13.46
        assert product_info.nutrition.fiber == 1.9
        assert product_info.nutrition.salt == 0.72
        assert product_info.nutrition.sodium == 0.288
        
        # Verify additives
        assert product_info.additives == ["e330"]
        
        # Verify score
        assert product_info.score == score
        
        # Verify image URL
        assert product_info.image_url == "https://example.com/image.jpg"

    def test_create_fallback_analysis(self):
        """Test fallback analysis creation."""
        analyzer = ProductAnalyzer(api_key="test_key")
        
        # Create fallback analysis
        result = analyzer._create_fallback_analysis(
            user_allergens=["Peanuts", "Dairy"],
            user_diets=["Vegetarian", "Gluten-Free"]
        )
        
        # Verify the structure
        assert isinstance(result, AIServiceOutput)
        assert result.allergens_analysis.detected_allergens == []
        assert result.allergens_analysis.user_allergens_present == []
        assert len(result.diet_compatibility) == 2
        assert result.diet_compatibility[0].diet == "Vegetarian"
        assert result.diet_compatibility[0].compatible is False
        assert "Unable to determine" in result.diet_compatibility[0].reason
        assert result.diet_compatibility[1].diet == "Gluten-Free"
        assert result.diet_compatibility[1].compatible is False
        assert result.score is None 