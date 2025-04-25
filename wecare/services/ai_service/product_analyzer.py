"""
High-level product analysis service using GPT-4.
Integrates GPT client with product analysis logic.
"""
import json
from typing import Dict, List, Any, Optional

from wecare.core.models.schemas import (
    AIServiceInput, 
    AIServiceOutput,
    ProductInfo,
    ProductAnalysis,
    Score
)
from wecare.core.scoring.scoring_engine import ScoringEngine
from wecare.services.ai_service.gpt_client import GPTClient
from wecare.utils.logger import get_logger


logger = get_logger(__name__)


class ProductAnalyzer:
    """Service for analyzing food products using AI."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, guided_json: Optional[Dict[str, Any]] = None):
        """Initialize product analyzer.
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
            guided_json: Optional JSON schema template to guide the model's responses.
                        If None, uses GPTClient's default schema.
        """
        self.gpt_client = GPTClient(api_key=api_key, model=model, guided_json=guided_json)
    
    def analyze_product(
        self, 
        product_info: Dict[str, Any],
        user_allergens: List[str],
        user_diets: List[str],
        use_ai_scoring: bool = True
    ) -> ProductAnalysis:
        """Analyze product with GPT and create full product analysis.
        
        Args:
            product_info: Product information from external service
            user_allergens: List of user's allergens
            user_diets: List of user's dietary preferences
            use_ai_scoring: Whether to use AI for scoring (if False, uses local scoring engine)
            
        Returns:
            Complete product analysis with AI-generated insights
        """
        logger.info(f"Analyzing product: {product_info.get('name', 'Unknown')}")
        
        # Determine if we need GPT to calculate the score
        external_score_available = "score" in product_info and product_info.get("score") is not None
        calculate_score = not external_score_available and use_ai_scoring
        
        # Create input for GPT
        ai_input = AIServiceInput(
            product_info=product_info,
            user_allergens=user_allergens,
            user_diets=user_diets,
            calculate_score=calculate_score
        )
        
        # Get AI analysis
        try:
            ai_output = self.gpt_client.analyze_product(ai_input)
            logger.debug("GPT analysis completed successfully")
        except Exception as e:
            logger.error(f"Error during GPT analysis: {str(e)}")
            # Provide fallback values if GPT fails
            ai_output = self._create_fallback_analysis(
                user_allergens=user_allergens,
                user_diets=user_diets
            )
        
        # Determine which scoring method to use
        if external_score_available:
            # Use score from product info
            logger.debug("Using score from external service")
            score_data = product_info.get("score", {})
            product_score = Score(
                total=score_data.get("total", 50),
                category=score_data.get("category", "Average"),
                nutrition_score=score_data.get("nutrition_score", 30),
                additives_score=score_data.get("additives_score", 20)
            )
        elif use_ai_scoring and ai_output.score:
            # Use AI-generated score if requested and available
            logger.debug("Using GPT-generated score")
            product_score = ai_output.score
        else:
            # Use local scoring engine
            logger.debug("Calculating score with scoring engine")
            product_score = ScoringEngine.calculate_score(product_info)
        
        # Create product info object
        processed_product = self._create_product_info(product_info, product_score)
        
        # Create final product analysis
        return ProductAnalysis(
            product=processed_product,
            allergens_analysis=ai_output.allergens_analysis,
            diet_compatibility=ai_output.diet_compatibility
        )
    
    def _create_product_info(self, product_data: Dict[str, Any], score: Score) -> ProductInfo:
        """Create ProductInfo object from raw product data from Open Food Facts API.
        
        Args:
            product_data: Raw product data from Open Food Facts API
            score: Product score
            
        Returns:
            Structured ProductInfo object
        """
        # Extract product section from Open Food Facts response
        off_product = product_data.get("product", product_data)
        
        # Parse weight information
        weight_str = off_product.get("quantity", "0 g")
        weight_value = 0.0
        weight_unit = "g"
        
        # Try to extract numeric value and unit from quantity string
        import re
        weight_match = re.match(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)", weight_str)
        if weight_match:
            weight_value = float(weight_match.group(1))
            weight_unit = weight_match.group(2).lower()
        
        # Create Weight object
        from wecare.core.models.schemas import Weight
        weight = Weight(value=weight_value, unit=weight_unit)
        
        # Extract ingredients
        ingredients_list = []
        if "ingredients" in off_product:
            from wecare.core.models.schemas import Ingredient
            for ing in off_product.get("ingredients", []):
                # Determine safety classification based on additives lists
                safety = "safe"
                ing_id = ing.get("id", "")
                if ing_id.startswith("en:e") and ing_id in off_product.get("additives_tags", []):
                    if ing_id in product_data.get("harmful_additives", []):
                        safety = "harmful"
                    elif ing_id in product_data.get("suspicious_additives", []):
                        safety = "suspicious"
                
                ingredients_list.append(Ingredient(
                    name=ing.get("text", ""),
                    safety=safety
                ))
        
        # Extract nutrition information
        nutriments = off_product.get("nutriments", {})
        
        # Extract additives
        additives = [
            additive.replace("en:", "") 
            for additive in off_product.get("additives_tags", [])
        ]
        
        # Create the nutrition info structure
        from wecare.core.models.schemas import NutritionInfo, FatInfo, CarbInfo
        
        fat_info = FatInfo(
            total=nutriments.get("fat_100g", nutriments.get("fat", 0)),
            saturated=nutriments.get("saturated-fat_100g", nutriments.get("saturated-fat", 0))
        )
        
        carb_info = CarbInfo(
            total=nutriments.get("carbohydrates_100g", nutriments.get("carbohydrates", 0)),
            sugar=nutriments.get("sugars_100g", nutriments.get("sugars", 0))
        )
        
        nutrition = NutritionInfo(
            calories=nutriments.get("energy-kcal_100g", nutriments.get("energy-kcal", 0)),
            protein=nutriments.get("proteins_100g", nutriments.get("proteins", 0)),
            fat=fat_info,
            carbohydrates=carb_info,
            fiber=nutriments.get("fiber_100g", nutriments.get("fiber", 0)),
            salt=nutriments.get("salt_100g", nutriments.get("salt", 0)),
            sodium=nutriments.get("sodium_100g", nutriments.get("sodium", 0))
        )
        
        # Return the structured ProductInfo object
        return ProductInfo(
            id=off_product.get("_id", off_product.get("id", "unknown")),
            barcode=off_product.get("code", "unknown"),
            name=off_product.get("product_name", off_product.get("product_name_en", "Unknown Product")),
            manufacturer=off_product.get("brand_owner", off_product.get("brands", "Unknown")),
            weight=weight,
            ingredients=ingredients_list,
            nutrition=nutrition,
            score=score,
            additives=additives,
            image_url=off_product.get("image_url", off_product.get("image_front_url", None))
        )
    
    def _create_fallback_analysis(
        self, 
        user_allergens: List[str],
        user_diets: List[str]
    ) -> AIServiceOutput:
        """Create fallback analysis when GPT fails.
        
        Args:
            user_allergens: List of user's allergens
            user_diets: List of user's dietary preferences
            
        Returns:
            Basic fallback analysis
        """
        from wecare.core.models.schemas import AllergenAnalysis, DietCompatibility
        
        logger.warning("Using fallback analysis")
        
        return AIServiceOutput(
            allergens_analysis=AllergenAnalysis(
                detected_allergens=[],
                user_allergens_present=[]
            ),
            diet_compatibility=[
                DietCompatibility(
                    diet=diet,
                    compatible=False,
                    reason="Unable to determine compatibility due to analysis error"
                )
                for diet in user_diets
            ],
            score=None
        ) 