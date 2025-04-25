"""Unit tests for the GPT client."""
import json
import pytest
from unittest.mock import MagicMock, patch

from wecare.services.ai_service.gpt_client import GPTClient
from wecare.core.models.schemas import AIServiceInput


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    client = MagicMock()
    
    # Create a mock response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    # Sample response content
    response_content = {
            "allergens_analysis": {
            "detected_allergens": ["Peanuts", "Soybeans"],
                "user_allergens_present": ["Peanuts"]
            },
            "diet_compatibility": [
                {
                    "diet": "Vegetarian",
                    "compatible": True,
                    "reason": "Contains no meat or animal products"
                },
                {
                    "diet": "Low-Sugar",
                    "compatible": False,
                    "reason": "Contains more than 5g of sugar per 100g"
                }
            ],
            "score": {
                "total": 75,
                "category": "Good",
                "nutrition_score": 80,
                "additives_score": 70
            }
        }
    
    mock_message.content = json.dumps(response_content)
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    client.chat.completions.create.return_value = mock_response
    
    return client


@pytest.fixture
def mock_openai_response(mock_openai_client):
    """Return the mock response from the OpenAI client."""
    return mock_openai_client.chat.completions.create.return_value


class TestGPTClient:
    """Test suite for the GPT client."""
    
    @patch("wecare.services.ai_service.gpt_client.OpenAI")
    def test_initialization(self, mock_openai):
        """Test GPT client initialization."""
        # Test with default parameters
        client = GPTClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.model is not None
        assert client.base_url is not None
        assert client.guided_json is not None
        mock_openai.assert_called_once()

    @patch("wecare.services.ai_service.gpt_client.OpenAI")
    def test_initialization_custom_parameters(self, mock_openai):
        """Test GPT client initialization with custom parameters."""
        guided_json = {"custom": "template"}
        
        client = GPTClient(
            api_key="test_key",
            model="custom-model",
            base_url="https://custom-url.example.com",
            guided_json=guided_json
        )
        
        assert client.api_key == "test_key"
        assert client.model == "custom-model"
        assert client.base_url == "https://custom-url.example.com"
        assert client.guided_json == guided_json
        mock_openai.assert_called_once()
        
    @patch("wecare.services.ai_service.gpt_client.OpenAI")
    def test_initialization_missing_api_key(self, mock_openai):
        """Test error handling when API key is missing."""
        # Mock settings.OPENAI_API_KEY to be empty
        with patch("wecare.services.ai_service.gpt_client.settings.OPENAI_API_KEY", ""):
            with pytest.raises(ValueError) as excinfo:
                GPTClient()
            
            assert "API key is required" in str(excinfo.value)

    def test_create_prompt(self):
        """Test prompt creation."""
        # Create a simple input
        input_data = AIServiceInput(
            product_info={"name": "Test Product", "ingredients": ["Sugar", "Water"]},
            user_allergens=["Peanuts", "Shellfish"],
            user_diets=["Vegetarian", "Low-Sugar"],
            calculate_score=True
        )
        
        client = GPTClient(api_key="test_key")
        prompt = client._create_prompt(input_data)
        
        # Check that the prompt contains the expected elements
        assert "Test Product" in prompt
        assert "Peanuts, Shellfish" in prompt
        assert "Vegetarian, Low-Sugar" in prompt
        assert "Calculate a product quality score" in prompt
        assert "schema" in prompt

    def test_create_prompt_no_score(self):
        """Test prompt creation without scoring."""
        # Create input without score calculation
        input_data = AIServiceInput(
            product_info={"name": "Test Product", "ingredients": ["Sugar", "Water"]},
            user_allergens=["Peanuts"],
            user_diets=["Vegetarian"],
            calculate_score=False
        )
        
        client = GPTClient(api_key="test_key")
        prompt = client._create_prompt(input_data)
        
        # Check that the prompt doesn't request scoring
        assert "Calculate a product quality score" not in prompt
        assert "schema" in prompt

    def test_analyze_product(self, mock_openai_client):
        """Test product analysis with mocked OpenAI client."""
        with patch("wecare.services.ai_service.gpt_client.OpenAI", return_value=mock_openai_client):
            client = GPTClient(api_key="test_key")
            
            # Create a test input
            input_data = AIServiceInput(
                product_info={"name": "Test Product", "ingredients": ["Sugar", "Water"]},
                user_allergens=["Peanuts"],
                user_diets=["Vegetarian", "Low-Sugar"],
                calculate_score=True
            )
            
            # Analyze the product
            result = client.analyze_product(input_data)
            
            # Verify the client was called with expected parameters
            mock_openai_client.chat.completions.create.assert_called_once()
            call_args = mock_openai_client.chat.completions.create.call_args[1]
            assert call_args["model"] == client.model
            assert len(call_args["messages"]) == 2
            assert call_args["messages"][0]["role"] == "system"
            assert call_args["messages"][1]["role"] == "user"
            assert call_args["response_format"] == {"type": "json_object"}
            
            # Verify the result structure
            assert result.allergens_analysis.detected_allergens == ["Peanuts", "Soybeans"]
            assert result.allergens_analysis.user_allergens_present == ["Peanuts"]
            assert len(result.diet_compatibility) == 2
            assert result.diet_compatibility[0].diet == "Vegetarian"
            assert result.diet_compatibility[0].compatible is True
            assert result.diet_compatibility[1].diet == "Low-Sugar"
            assert result.diet_compatibility[1].compatible is False
            assert result.score is not None
            assert result.score.total == 75
            assert result.score.category == "Good"

    def test_analyze_product_without_scoring(self, mock_openai_client):
        """Test product analysis without score calculation."""
        with patch("wecare.services.ai_service.gpt_client.OpenAI", return_value=mock_openai_client):
            client = GPTClient(api_key="test_key")
            
            # Create a test input without score calculation
            input_data = AIServiceInput(
                product_info={"name": "Test Product", "ingredients": ["Sugar", "Water"]},
                user_allergens=["Peanuts"],
                user_diets=["Vegetarian", "Low-Sugar"],
                calculate_score=False
            )
            
            # Analyze the product
            result = client.analyze_product(input_data)
            
            # Verify the client was called with expected parameters
            mock_openai_client.chat.completions.create.assert_called_once()
            
            # Verify the result structure
            assert result.allergens_analysis.detected_allergens == ["Peanuts", "Soybeans"]
            assert result.allergens_analysis.user_allergens_present == ["Peanuts"]
            assert len(result.diet_compatibility) == 2
            assert result.diet_compatibility[0].diet == "Vegetarian"
            assert result.diet_compatibility[0].compatible is True
            assert result.diet_compatibility[1].diet == "Low-Sugar"
            assert result.diet_compatibility[1].compatible is False
            # Score should still be provided in our mock
            assert result.score is not None
            assert result.score.total == 75
            assert result.score.category == "Good"
            
    def test_analyze_product_error_handling(self, mock_openai_client):
        """Test error handling during product analysis."""
        # Configure the mock to raise an exception
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch("wecare.services.ai_service.gpt_client.OpenAI", return_value=mock_openai_client):
            client = GPTClient(api_key="test_key")
            
            # Create a test input
            input_data = AIServiceInput(
                product_info={"name": "Test Product", "ingredients": ["Sugar", "Water"]},
                user_allergens=["Peanuts"],
                user_diets=["Vegetarian", "Low-Sugar"],
                calculate_score=True
            )
            
            # Test that the exception is raised and properly handled
            with pytest.raises(Exception) as exc_info:
                client.analyze_product(input_data)
            
            assert "API Error" in str(exc_info.value)
            
    def test_analyze_product_response_without_score(self, mock_openai_client):
        """Test handling of response without score information."""
        # Create a modified response without score
        response_without_score = MagicMock()
        response_without_score.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "allergens_analysis": {
                            "detected_allergens": ["Peanuts", "Soybeans"],
                            "user_allergens_present": ["Peanuts"]
                        },
                        "diet_compatibility": [
                            {"diet": "Vegetarian", "compatible": True, "reason": "No animal products."},
                            {"diet": "Low-Sugar", "compatible": False, "reason": "High in sugar."}
                        ]
                        # No score section
                    })
                )
            )
        ]
        mock_openai_client.chat.completions.create.return_value = response_without_score
        
        with patch("wecare.services.ai_service.gpt_client.OpenAI", return_value=mock_openai_client):
            client = GPTClient(api_key="test_key")
            
            # Create a test input explicitly not requesting score
            input_data = AIServiceInput(
                product_info={"name": "Test Product", "ingredients": ["Sugar", "Water"]},
                user_allergens=["Peanuts"],
                user_diets=["Vegetarian", "Low-Sugar"],
                calculate_score=False
            )
            
            # Analyze the product
            result = client.analyze_product(input_data)
            
            # Verify the result structure has no score
            assert result.allergens_analysis.detected_allergens == ["Peanuts", "Soybeans"]
            assert result.allergens_analysis.user_allergens_present == ["Peanuts"]
            assert len(result.diet_compatibility) == 2
            assert result.diet_compatibility[0].diet == "Vegetarian"
            assert result.diet_compatibility[0].compatible is True
            assert result.diet_compatibility[1].diet == "Low-Sugar"
            assert result.diet_compatibility[1].compatible is False
            assert result.score is None 