"""
Scoring engine for evaluating product quality.
Used when scoring is not provided by external service.
"""
from typing import Dict, List, Tuple, Any, Optional
import logging

from wecare.core.models.schemas import Score, NutritionInfo, Ingredient


logger = logging.getLogger(__name__)


class ScoringError(Exception):
    """Exception raised for errors in the scoring process."""
    pass


class ScoringEngine:
    """Engine for calculating product quality scores."""
    
    # Score category thresholds
    SCORE_CATEGORIES = {
        (81, 100): "Excellent",
        (61, 80): "Good",
        (41, 60): "Average",
        (21, 40): "Low Quality",
        (0, 20): "Very Low Quality"
    }
    
    # Nutritional value weights (60% of total)
    NUTRITION_WEIGHTS = {
        "proteins": 0.2,
        "fats": 0.2,
        "carbs": 0.2,
        "fiber": 0.1,
        "salt": 0.1,
        "calories": 0.2
    }
    
    # Additives weights (40% of total)
    ADDITIVES_WEIGHTS = {
        "safe": 0.4,
        "suspicious": 0.3,
        "harmful": 0.3
    }
    
    # Overall weights
    OVERALL_WEIGHTS = {
        "nutrition": 0.6,
        "additives": 0.4
    }
    
    # Nutrition content thresholds (these would ideally be calibrated by nutritionists)
    PROTEIN_THRESHOLDS = {"high": 5.0, "medium": 2.5}  # grams per 100g
    FAT_THRESHOLDS = {"high": 17.5, "medium": 5.0}  # grams per 100g
    SATURATED_FAT_THRESHOLDS = {"high": 5.0, "medium": 1.5}  # grams per 100g
    SUGAR_THRESHOLDS = {"high": 22.5, "medium": 5.0}  # grams per 100g
    FIBER_THRESHOLDS = {"high": 6.0, "medium": 3.0}  # grams per 100g
    SALT_THRESHOLDS = {"high": 1.5, "medium": 0.3}  # grams per 100g
    CALORIE_THRESHOLDS = {"high": 400, "medium": 200}  # kcal per 100g
    
    @staticmethod
    def get_score_category(score: int) -> str:
        """Get score category based on numeric score.
        
        Args:
            score: Numeric score (0-100)
            
        Returns:
            Category string
            
        Raises:
            ScoringError: If score is outside the valid range
        """
        for score_range, category in ScoringEngine.SCORE_CATEGORIES.items():
            if score_range[0] <= score <= score_range[1]:
                return category
        
        raise ScoringError(f"Score {score} is outside the valid range (0-100)")
    
    @classmethod
    def calculate_score(cls, product_data: Dict[str, Any]) -> Score:
        """Calculate product quality score.
        
        Args:
            product_data: Dictionary containing product information
            
        Returns:
            Score object with total score and category
            
        Raises:
            ScoringError: If required product data is missing or invalid
        """
        if not product_data:
            raise ScoringError("Product data is missing")
        
        # Calculate nutrition score (out of 100)
        try:
            nutrition_score = cls._calculate_nutrition_score(product_data)
        except Exception as e:
            raise ScoringError(f"Failed to calculate nutrition score: {str(e)}")
        
        # Calculate additives score (out of 100)
        try:
            additives_score = cls._calculate_additives_score(product_data)
        except Exception as e:
            raise ScoringError(f"Failed to calculate additives score: {str(e)}")
        
        # Calculate total score
        total_score = round(
            (nutrition_score * cls.OVERALL_WEIGHTS["nutrition"]) +
            (additives_score * cls.OVERALL_WEIGHTS["additives"])
        )
        
        # Get category
        category = cls.get_score_category(total_score)
        
        return Score(
            total=total_score,
            category=category,
            nutrition_score=round(nutrition_score),
            additives_score=round(additives_score)
        )
    
    @classmethod
    def _calculate_nutrition_score(cls, product_data: Dict[str, Any]) -> float:
        """Calculate nutrition score component based on WHO recommendations.
        
        Args:
            product_data: Dictionary containing product nutrition information
            
        Returns:
            Nutrition score (0-100)
            
        Raises:
            ScoringError: If nutrition data is missing or invalid
        """
        nutrition = product_data.get("nutrition")
        
        if not nutrition:
            raise ScoringError("Nutrition information is missing")
        
        # Calculate individual component scores
        scores = {}
        
        try:
            scores["proteins"] = cls._score_protein(nutrition)
            scores["fats"] = cls._score_fats(nutrition)
            scores["carbs"] = cls._score_carbs(nutrition)
            scores["fiber"] = cls._score_fiber(nutrition)
            scores["salt"] = cls._score_salt(nutrition)
            scores["calories"] = cls._score_calories(nutrition)
        except Exception as e:
            raise ScoringError(f"Error in nutrition scoring: {str(e)}")
        
        # Calculate weighted nutrition score
        weighted_score = sum(
            scores[component] * cls.NUTRITION_WEIGHTS[component]
            for component in scores
        )
        
        # Convert to scale of 0-100
        return weighted_score * 10
    
    @classmethod
    def _score_protein(cls, nutrition: Dict[str, Any]) -> float:
        """Score protein content from 0-10.
        
        Raises:
            ScoringError: If protein data is missing
        """
        if "protein" not in nutrition:
            raise ScoringError("Protein information is missing")
            
        protein = nutrition["protein"]
        
        if protein >= cls.PROTEIN_THRESHOLDS["high"]:
            return 10.0  # High protein content
        elif protein >= cls.PROTEIN_THRESHOLDS["medium"]:
            return 5.0   # Medium protein content
        else:
            return 0.0   # Low protein content
    
    @classmethod
    def _score_fats(cls, nutrition: Dict[str, Any]) -> float:
        """Score fat content from 0-10.
        
        Raises:
            ScoringError: If fat data is missing or invalid
        """
        if "fat" not in nutrition:
            raise ScoringError("Fat information is missing")
            
        fat_info = nutrition["fat"]
        
        if not isinstance(fat_info, dict):
            raise ScoringError("Fat information is not in the expected format")
            
        if "saturated" not in fat_info:
            raise ScoringError("Saturated fat information is missing")
            
        saturated_fat = fat_info["saturated"]
        
        if saturated_fat <= cls.SATURATED_FAT_THRESHOLDS["medium"]:
            return 10.0  # Low saturated fat
        elif saturated_fat <= cls.SATURATED_FAT_THRESHOLDS["high"]:
            return 5.0   # Medium saturated fat
        else:
            return 0.0   # High saturated fat
    
    @classmethod
    def _score_carbs(cls, nutrition: Dict[str, Any]) -> float:
        """Score carbohydrate content from 0-10.
        
        Raises:
            ScoringError: If carbohydrate data is missing or invalid
        """
        if "carbohydrates" not in nutrition:
            raise ScoringError("Carbohydrate information is missing")
            
        carb_info = nutrition["carbohydrates"]
        
        if not isinstance(carb_info, dict):
            raise ScoringError("Carbohydrate information is not in the expected format")
            
        if "sugar" not in carb_info:
            raise ScoringError("Sugar information is missing")
            
        sugar = carb_info["sugar"]
        
        if sugar <= cls.SUGAR_THRESHOLDS["medium"]:
            return 10.0  # Low sugar content
        elif sugar <= cls.SUGAR_THRESHOLDS["high"]:
            return 5.0   # Medium sugar content
        else:
            return 0.0   # High sugar content
    
    @classmethod
    def _score_fiber(cls, nutrition: Dict[str, Any]) -> float:
        """Score fiber content from 0-10.
        
        Raises:
            ScoringError: If fiber data is missing
        """
        if "fiber" not in nutrition:
            raise ScoringError("Fiber information is missing")
            
        fiber = nutrition["fiber"]
        
        if fiber >= cls.FIBER_THRESHOLDS["high"]:
            return 10.0  # High fiber content
        elif fiber >= cls.FIBER_THRESHOLDS["medium"]:
            return 5.0   # Medium fiber content
        else:
            return 0.0   # Low fiber content
    
    @classmethod
    def _score_salt(cls, nutrition: Dict[str, Any]) -> float:
        """Score salt content from 0-10.
        
        Raises:
            ScoringError: If salt data is missing
        """
        if "salt" not in nutrition:
            raise ScoringError("Salt information is missing")
            
        salt = nutrition["salt"]
        
        if salt <= cls.SALT_THRESHOLDS["medium"]:
            return 10.0  # Low salt content
        elif salt <= cls.SALT_THRESHOLDS["high"]:
            return 5.0   # Medium salt content
        else:
            return 0.0   # High salt content
    
    @classmethod
    def _score_calories(cls, nutrition: Dict[str, Any]) -> float:
        """Score calorie content from 0-10.
        
        Raises:
            ScoringError: If calorie data is missing
        """
        if "calories" not in nutrition:
            raise ScoringError("Calorie information is missing")
            
        calories = nutrition["calories"]
        
        if calories <= cls.CALORIE_THRESHOLDS["medium"]:
            return 10.0  # Low calorie content
        elif calories <= cls.CALORIE_THRESHOLDS["high"]:
            return 5.0   # Medium calorie content
        else:
            return 0.0   # High calorie content
    
    @classmethod
    def _calculate_additives_score(cls, product_data: Dict[str, Any]) -> float:
        """Calculate additives score based on E-codes classification.
        
        Args:
            product_data: Dictionary containing product additives information
            
        Returns:
            Additives score (0-100)
            
        Raises:
            ScoringError: If additives data is invalid
        """
        # Check that at least one of additives or ingredients is present
        if "additives" not in product_data and "ingredients" not in product_data:
            raise ScoringError("Both additives and ingredients information is missing")
        
        additives = product_data.get("additives", [])
        ingredients = product_data.get("ingredients", [])
        
        # Check for required additive lists
        if "safe_additives" not in product_data:
            raise ScoringError("Safe additives reference list is missing")
        if "suspicious_additives" not in product_data:
            raise ScoringError("Suspicious additives reference list is missing")
        if "harmful_additives" not in product_data:
            raise ScoringError("Harmful additives reference list is missing")
        
        # Get lists of safe, suspicious, and harmful additives
        safe_additives = set(product_data["safe_additives"])
        suspicious_additives = set(product_data["suspicious_additives"])
        harmful_additives = set(product_data["harmful_additives"])
        
        # Extract additives from ingredient list
        ingredient_additives = []
        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                raise ScoringError("Ingredient data is not in the expected format")
                
            if "name" not in ingredient:
                raise ScoringError("Ingredient name is missing")
                
            if ingredient["name"].startswith("E"):
                ingredient_additives.append(ingredient["name"])
        
        # Combine all additives
        all_additives = set(additives + ingredient_additives)
        
        # Calculate scores for each category
        safe_score = cls._score_safe_additives(all_additives, safe_additives)
        suspicious_score = cls._score_suspicious_additives(all_additives, suspicious_additives)
        harmful_score = cls._score_harmful_additives(all_additives, harmful_additives)
        
        # Calculate weighted additives score
        weighted_score = (
            safe_score * cls.ADDITIVES_WEIGHTS["safe"] +
            suspicious_score * cls.ADDITIVES_WEIGHTS["suspicious"] +
            harmful_score * cls.ADDITIVES_WEIGHTS["harmful"]
        )
        
        # Convert to scale of 0-100
        return weighted_score * 10
    
    @staticmethod
    def _score_safe_additives(all_additives: set, safe_additives: set) -> float:
        """Score safe additives from 0-10."""
        if not all_additives:
            # No additives is neutral for this score (product has no additives)
            return 5.0
        
        # Check if all additives are safe
        if all_additives.issubset(safe_additives):
            return 10.0  # Only beneficial additives
        
        # Check if any additives are safe
        if safe_additives.intersection(all_additives):
            return 5.0  # Some safe additives
        
        return 0.0  # No safe additives
    
    @staticmethod
    def _score_suspicious_additives(all_additives: set, suspicious_additives: set) -> float:
        """Score suspicious additives from 0-10."""
        if not all_additives:
            # No additives is neutral for this score (product has no additives)
            return 5.0
        
        # Check if no additives are suspicious
        if not suspicious_additives.intersection(all_additives):
            return 10.0  # No suspicious additives
        
        return 0.0  # Has suspicious additives
    
    @staticmethod
    def _score_harmful_additives(all_additives: set, harmful_additives: set) -> float:
        """Score harmful additives from 0-10."""
        if not all_additives:
            # No additives is neutral for this score (product has no additives)
            return 5.0
        
        # Check if no additives are harmful
        if not harmful_additives.intersection(all_additives):
            return 10.0  # No harmful additives
        
        return 0.0  # Has harmful additives 