"""Unit tests for the core data models."""
import pytest
from dataclasses import asdict

from wecare.core.models.schemas import (
    Weight, Ingredient, FatInfo, CarbInfo, NutritionInfo,
    Score, ProductInfo, AllergenAnalysis, DietCompatibility,
    ProductAnalysis, AIServiceInput, AIServiceOutput
)


class TestDataModels:
    """Test suite for data model structures."""

    def test_weight_initialization(self):
        """Test Weight dataclass initialization."""
        weight = Weight(value=100.0, unit="g")
        assert weight.value == 100.0
        assert weight.unit == "g"
        
        # Test dictionary conversion
        weight_dict = asdict(weight)
        assert weight_dict == {"value": 100.0, "unit": "g"}

    def test_ingredient_initialization(self):
        """Test Ingredient dataclass initialization."""
        ingredient = Ingredient(name="Sugar", safety="suspicious")
        assert ingredient.name == "Sugar"
        assert ingredient.safety == "suspicious"

    def test_fat_info_initialization(self):
        """Test FatInfo dataclass initialization."""
        fat_info = FatInfo(total=10.5, saturated=3.2)
        assert fat_info.total == 10.5
        assert fat_info.saturated == 3.2

    def test_carb_info_initialization(self):
        """Test CarbInfo dataclass initialization."""
        carb_info = CarbInfo(total=45.0, sugar=12.5)
        assert carb_info.total == 45.0
        assert carb_info.sugar == 12.5

    def test_nutrition_info_initialization(self):
        """Test NutritionInfo dataclass initialization."""
        fat = FatInfo(total=10.5, saturated=3.2)
        carbs = CarbInfo(total=45.0, sugar=12.5)
        nutrition = NutritionInfo(
            calories=350,
            protein=8.5,
            fat=fat,
            carbohydrates=carbs,
            fiber=2.5,
            salt=0.5,
            sodium=0.2
        )
        
        assert nutrition.calories == 350
        assert nutrition.protein == 8.5
        assert nutrition.fat is fat
        assert nutrition.carbohydrates is carbs
        assert nutrition.fiber == 2.5
        assert nutrition.salt == 0.5
        assert nutrition.sodium == 0.2

    def test_score_initialization(self):
        """Test Score dataclass initialization."""
        score = Score(total=85, category="Excellent", nutrition_score=90, additives_score=80)
        assert score.total == 85
        assert score.category == "Excellent"
        assert score.nutrition_score == 90
        assert score.additives_score == 80

    def test_product_info_initialization(self, sample_score):
        """Test ProductInfo dataclass initialization."""
        weight = Weight(value=200.0, unit="g")
        ingredients = [
            Ingredient(name="Water", safety="safe"),
            Ingredient(name="Sugar", safety="suspicious")
        ]
        fat = FatInfo(total=10.5, saturated=3.2)
        carbs = CarbInfo(total=45.0, sugar=12.5)
        nutrition = NutritionInfo(
            calories=350,
            protein=8.5,
            fat=fat,
            carbohydrates=carbs,
            fiber=2.5,
            salt=0.5,
            sodium=0.2
        )
        
        product = ProductInfo(
            id="123",
            barcode="0737628064502",
            name="Test Product",
            manufacturer="Test Company",
            weight=weight,
            ingredients=ingredients,
            nutrition=nutrition,
            score=sample_score,
            additives=["E330", "E202"],
            image_url="https://example.com/image.jpg"
        )
        
        assert product.id == "123"
        assert product.barcode == "0737628064502"
        assert product.name == "Test Product"
        assert product.manufacturer == "Test Company"
        assert product.weight is weight
        assert product.ingredients == ingredients
        assert product.nutrition is nutrition
        assert product.score is sample_score
        assert product.additives == ["E330", "E202"]
        assert product.image_url == "https://example.com/image.jpg"

    def test_allergen_analysis_initialization(self):
        """Test AllergenAnalysis dataclass initialization."""
        analysis = AllergenAnalysis(
            detected_allergens=["Peanuts", "Soybeans", "Gluten"],
            user_allergens_present=["Peanuts"]
        )
        
        assert analysis.detected_allergens == ["Peanuts", "Soybeans", "Gluten"]
        assert analysis.user_allergens_present == ["Peanuts"]

    def test_diet_compatibility_initialization(self):
        """Test DietCompatibility dataclass initialization."""
        compatibility = DietCompatibility(
            diet="Vegan",
            compatible=False,
            reason="Contains animal products"
        )
        
        assert compatibility.diet == "Vegan"
        assert compatibility.compatible is False
        assert compatibility.reason == "Contains animal products"

    def test_product_analysis_initialization(self, sample_product_info, sample_allergen_analysis):
        """Test ProductAnalysis dataclass initialization."""
        diet_compatibility = [
            DietCompatibility(diet="Vegan", compatible=True, reason="All plant-based"),
            DietCompatibility(diet="Gluten-Free", compatible=False, reason="Contains wheat")
        ]
        
        analysis = ProductAnalysis(
            product=sample_product_info,
            allergens_analysis=sample_allergen_analysis,
            diet_compatibility=diet_compatibility
        )
        
        assert analysis.product is sample_product_info
        assert analysis.allergens_analysis is sample_allergen_analysis
        assert analysis.diet_compatibility == diet_compatibility

    def test_ai_service_input_initialization(self):
        """Test AIServiceInput dataclass initialization."""
        product_info = {"name": "Test Product", "ingredients": ["Sugar", "Water"]}
        
        service_input = AIServiceInput(
            product_info=product_info,
            user_allergens=["Peanuts", "Shellfish"],
            user_diets=["Vegan", "Gluten-Free"],
            calculate_score=True
        )
        
        assert service_input.product_info is product_info
        assert service_input.user_allergens == ["Peanuts", "Shellfish"]
        assert service_input.user_diets == ["Vegan", "Gluten-Free"]
        assert service_input.calculate_score is True

    def test_ai_service_output_initialization(self, sample_allergen_analysis, sample_score):
        """Test AIServiceOutput dataclass initialization."""
        diet_compatibility = [
            DietCompatibility(diet="Vegan", compatible=True, reason="All plant-based"),
            DietCompatibility(diet="Gluten-Free", compatible=False, reason="Contains wheat")
        ]
        
        service_output = AIServiceOutput(
            allergens_analysis=sample_allergen_analysis,
            diet_compatibility=diet_compatibility,
            score=sample_score
        )
        
        assert service_output.allergens_analysis is sample_allergen_analysis
        assert service_output.diet_compatibility == diet_compatibility
        assert service_output.score is sample_score
        
        # Test with optional score
        service_output_no_score = AIServiceOutput(
            allergens_analysis=sample_allergen_analysis,
            diet_compatibility=diet_compatibility,
            score=None
        )
        
        assert service_output_no_score.score is None 