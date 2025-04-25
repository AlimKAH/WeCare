"""
GPT-4 client for WeCare application.
Handles communication with OpenAI API for product analysis.
"""
import json
import logging
import os
from typing import Dict, List, Any, Optional

import openai
from openai import OpenAI

from wecare.config import settings
from wecare.core.models.schemas import (
    AIServiceInput, 
    AIServiceOutput,
    AllergenAnalysis,
    DietCompatibility,
    Score
)

logger = logging.getLogger(__name__)


class GPTClient:
    """Client for interacting with OpenAI GPT models via LiteLLM proxy."""
    
    # Default JSON schema template for consistent responses
    DEFAULT_RESPONSE_SCHEMA = {
        "allergens_analysis": {
            "detected_allergens": ["list of allergens in product"],
            "user_allergens_present": ["list of user allergens found in product"]
        },
        "diet_compatibility": [
            {
                "diet": "name of diet",
                "compatible": True,
                "reason": "explanation"
            }
        ],
        "score": {
            "total": 0,
            "category": "category name",
            "nutrition_score": 0,
            "additives_score": 0
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, guided_json: Optional[Dict] = None):
        """Initialize GPT client with API key and model.
        
        Args:
            api_key: API key for the proxy. If not provided, will use OPENAI_API_KEY from settings.
            model: GPT model to use, defaults to OPENAI_MODEL from settings.
            base_url: Base URL for the LiteLLM proxy server, defaults to LLM_API_BASE_URL from settings.
            guided_json: Optional JSON schema template to guide the model's responses. If None, uses DEFAULT_RESPONSE_SCHEMA.
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.model = model or settings.OPENAI_MODEL
        self.base_url = base_url or settings.LLM_API_BASE_URL
        self.guided_json = guided_json or self.DEFAULT_RESPONSE_SCHEMA
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
    def _create_prompt(self, input_data: AIServiceInput) -> str:
        """Create a prompt for GPT based on product info and user preferences.
        
        Args:
            input_data: Input data including product info and user preferences.
            
        Returns:
            Formatted prompt string for GPT.
        """
        product_info = json.dumps(input_data.product_info, indent=2)
        user_allergens = ", ".join(input_data.user_allergens) if input_data.user_allergens else "None"
        user_diets = ", ".join(input_data.user_diets) if input_data.user_diets else "None"
        
        # Generate response schema based on whether score is needed
        response_schema = self.guided_json.copy()
        if not input_data.calculate_score and "score" in response_schema:
            response_schema.pop("score")
        
        schema_str = json.dumps(response_schema, indent=2)
        
        prompt = f"""
        Analyze the following food product information and provide:
        
        1. Allergen analysis 
        2. Diet compatibility assessment
        {f"3. Calculate a product quality score (0-100)" if input_data.calculate_score else ""}
        
        PRODUCT INFORMATION:
        {product_info}
        
        USER ALLERGENS: {user_allergens}
        
        USER DIETARY PREFERENCES: {user_diets}
        
        SCORING GUIDELINES (if needed):
        - Nutritional value (60% of total): Evaluate proteins, fats, carbs, fiber, salt, calories
        - Additives (40% of total): Evaluate E-codes and other additives
        - Final score should be 0-100 with categories: Excellent (81-100), Good (61-80), Average (41-60), Low Quality (21-40), Very Low Quality (0-20)
        
        Be comprehensive in allergen detection. Only include user allergens that are actually present in the product.
        
        Respond with a JSON object matching this exact schema:
        ```
        {schema_str}
        ```
        
        Strictly adhere to this schema to ensure consistent responses.
        """
        return prompt
    
    def analyze_product(self, input_data: AIServiceInput) -> AIServiceOutput:
        """Analyze product using GPT-4.
        
        Args:
            input_data: Product information and user preferences.
            
        Returns:
            Analysis including allergen info, diet compatibility, and optional score.
        """
        prompt = self._create_prompt(input_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise nutrition analysis assistant that replies only with JSON."},
                    {"role": "user", "content": prompt}     
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response received from API")
            result = json.loads(content)
            
            # Create output object
            allergens_analysis: AllergenAnalysis = AllergenAnalysis(
                detected_allergens=result["allergens_analysis"]["detected_allergens"],
                user_allergens_present=result["allergens_analysis"]["user_allergens_present"]
            )
            
            diet_compatibility = [
                DietCompatibility(
                    diet=item["diet"],
                    compatible=item["compatible"],
                    reason=item["reason"]
                )
                for item in result["diet_compatibility"]
            ]
            
            score = None
            if "score" in result:
                score = Score(
                    total=result["score"]["total"],
                    category=result["score"]["category"],
                    nutrition_score=result["score"]["nutrition_score"],
                    additives_score=result["score"]["additives_score"]
                )
            
            return AIServiceOutput(
                allergens_analysis=allergens_analysis,
                diet_compatibility=diet_compatibility,
                score=score
            )
            
        except Exception as e:
            logger.error(f"Error in GPT analysis: {str(e)}")
            raise 