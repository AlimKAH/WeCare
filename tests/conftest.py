"""Pytest configuration and shared fixtures."""
import json
import os
from unittest.mock import MagicMock, patch
import pytest

from wecare.core.models.schemas import (
    Score, ProductInfo, NutritionInfo, FatInfo, CarbInfo, Weight,
    AllergenAnalysis, DietCompatibility, ProductAnalysis
)


@pytest.fixture
def sample_product_data():
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


@pytest.fixture
def sample_nutrition_data():
    """Fixture providing sample nutrition data."""
    return {
        "calories": 385,
        "protein": 9.62,
        "fat": {
            "total": 7.69,
            "saturated": 1.92
        },
        "carbohydrates": {
            "total": 71.15,
            "sugar": 13.46
        },
        "fiber": 1.9,
        "salt": 0.72,
        "sodium": 0.288
    }


@pytest.fixture
def sample_score():
    """Fixture providing a sample score object."""
    return Score(
        total=75,
        category="Good",
        nutrition_score=80,
        additives_score=70
    )


@pytest.fixture
def sample_product_info(sample_score):
    """Fixture providing a sample ProductInfo object."""
    return ProductInfo(
        id="0737628064502",
        barcode="0737628064502",
        name="Thai peanut noodle kit",
        manufacturer="Simply Asia Foods, Inc.",
        weight=Weight(value=155.0, unit="g"),
        ingredients=[],
        nutrition=NutritionInfo(
            calories=385,
            protein=9.62,
            fat=FatInfo(total=7.69, saturated=1.92),
            carbohydrates=CarbInfo(total=71.15, sugar=13.46),
            fiber=1.9,
            salt=0.72,
            sodium=0.288
        ),
        score=sample_score,
        additives=["E330"],
        image_url="https://example.com/image.jpg"
    )


@pytest.fixture
def sample_allergen_analysis():
    """Fixture providing a sample AllergenAnalysis object."""
    return AllergenAnalysis(
        detected_allergens=["Peanuts", "Soybeans"],
        user_allergens_present=["Peanuts"]
    )


@pytest.fixture
def sample_diet_compatibility():
    """Fixture providing sample DietCompatibility objects."""
    return [
        DietCompatibility(
            diet="Vegetarian",
            compatible=True,
            reason="Contains no meat products"
        ),
        DietCompatibility(
            diet="Low-Sugar",
            compatible=False,
            reason="Contains 13.46g of sugar per 100g, which exceeds the limit for a low-sugar diet"
        )
    ]


@pytest.fixture
def sample_product_analysis(sample_product_info, sample_allergen_analysis, sample_diet_compatibility):
    """Fixture providing a sample ProductAnalysis object."""
    return ProductAnalysis(
        product=sample_product_info,
        allergens_analysis=sample_allergen_analysis,
        diet_compatibility=sample_diet_compatibility
    )


@pytest.fixture
def mock_openai_response():
    """Fixture providing a mock OpenAI API response."""
    class MockResponse:
        def __init__(self):
            self.choices = [
                MagicMock(
                    message=MagicMock(
                        content=json.dumps({
                            "allergens_analysis": {
                                "detected_allergens": ["Peanuts", "Soybeans"],
                                "user_allergens_present": ["Peanuts"]
                            },
                            "diet_compatibility": [
                                {
                                    "diet": "Vegetarian",
                                    "compatible": True,
                                    "reason": "Contains no meat products"
                                },
                                {
                                    "diet": "Low-Sugar",
                                    "compatible": False,
                                    "reason": "Contains 13.46g of sugar per 100g, which exceeds the limit for a low-sugar diet"
                                }
                            ],
                            "score": {
                                "total": 75,
                                "category": "Good",
                                "nutrition_score": 80,
                                "additives_score": 70
                            }
                        })
                    )
                )
            ]
    
    return MockResponse()


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Fixture providing a mock OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    return mock_client 