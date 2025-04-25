"""
Example of using the WeCare AI product analysis.

This script demonstrates how to:
1. Parse product data from external service
2. Send it for analysis to ChatGPT
3. Get allergen and diet compatibility results
"""
import json
import os
import sys
from typing import Dict, List, Any

# Add the project root to the path so Python can find the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wecare.services.ai_service.product_analyzer import ProductAnalyzer
from wecare.core.scoring.scoring_engine import ScoringEngine
from wecare.utils.logger import setup_logging, get_logger
from wecare.config import settings

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Define scoring references for detailed scoring evaluation
SAFE_ADDITIVES = settings.SAFE_ADDITIVES
SUSPICIOUS_ADDITIVES = settings.SUSPICIOUS_ADDITIVES
HARMFUL_ADDITIVES = settings.HARMFUL_ADDITIVES

# Define a custom guided JSON template for consistent AI responses
GUIDED_JSON_TEMPLATE = {
    "allergens_analysis": {
        "detected_allergens": ["List all detected allergens, be comprehensive"],
        "user_allergens_present": ["Only include user allergens that are actually present"]
    },
    "diet_compatibility": [
        {
            "diet": "Name of diet from user preferences",
            "compatible": "true or false based on ingredients",
            "reason": "Clear explanation of compatibility with specific ingredients mentioned"
        }
    ],
    "score": {
        "total": "0-100 score based on guidelines",
        "category": "Excellent/Good/Average/Low Quality/Very Low Quality",
        "nutrition_score": "0-100 score for nutritional value",
        "additives_score": "0-100 score for additives safety"
    }
}

# Sample product data (would come from external service)
SAMPLE_PRODUCT = {
    "id": "0737628064502",
    "barcode": "0737628064502",
    "name": "Thai peanut noodle kit includes stir-fry rice noodles & thai peanut seasoning",
    "manufacturer": "Simply Asia Foods, Inc.",
    "weight": {
        "value": 155,
        "unit": "g"
    },
    "ingredients": [
        {
            "name": "Rice Noodles (rice, water)",
            "safety": "safe"
        },
        {
            "name": "peanut",
            "safety": "safe"
        },
        {
            "name": "sugar",
            "safety": "suspicious"
        },
        {
            "name": "salt",
            "safety": "safe"
        },
        {
            "name": "corn starch",
            "safety": "safe"
        },
        {
            "name": "spices (chili, cinnamon, pepper, cumin, clove)",
            "safety": "safe"
        },
        {
            "name": "hydrolyzed soy protein",
            "safety": "suspicious"
        },
        {
            "name": "green onions",
            "safety": "safe"
        },
        {
            "name": "citric acid",
            "safety": "safe"
        },
        {
            "name": "peanut oil",
            "safety": "safe"
        },
        {
            "name": "sesame oil",
            "safety": "safe"
        },
        {
            "name": "natural flavor",
            "safety": "suspicious"
        }
    ],
    "nutrition": {
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
    },
    "additives": ["E330 (citric acid)"],
    "image_url": "https://images.openfoodfacts.org/images/products/073/762/806/4502/front_en.6.400.jpg",
    # Add reference lists for scoring calculation
    "safe_additives": SAFE_ADDITIVES,
    "suspicious_additives": SUSPICIOUS_ADDITIVES,
    "harmful_additives": HARMFUL_ADDITIVES
}

# Sample user preferences
USER_ALLERGENS = ["Peanuts", "Shellfish"]
USER_DIETS = ["Vegetarian", "Low-Sugar"]


def main():
    """Run the example."""
    logger.info("Starting WeCare AI product analysis example")
    
    # Make sure API key is set
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.info("Set the OPENAI_API_KEY environment variable and try again")
        logger.info("Example: export OPENAI_API_KEY=your_key_here")
        return
    
    # Create product analyzer with settings and guided JSON template
    logger.info("Creating ProductAnalyzer with guided JSON template for consistent AI responses")
    analyzer = ProductAnalyzer(guided_json=GUIDED_JSON_TEMPLATE)
    
    # First case: product with score missing - will use GPT to generate score
    logger.info("CASE 1: Analyzing product with missing score - GPT will generate")
    product_without_score = SAMPLE_PRODUCT.copy()
    if "score" in product_without_score:
        del product_without_score["score"]
    
    result1 = analyzer.analyze_product(
        product_info=product_without_score,
        user_allergens=USER_ALLERGENS,
        user_diets=USER_DIETS,
        use_ai_scoring=True
    )
    
    # Second case: product with score - will use existing score
    logger.info("CASE 2: Analyzing product with existing score")
    product_with_score = SAMPLE_PRODUCT.copy()
    product_with_score["score"] = {
        "total": 83,
        "category": "Excellent",
        "nutrition_score": 51,
        "additives_score": 32
    }
    
    result2 = analyzer.analyze_product(
        product_info=product_with_score,
        user_allergens=USER_ALLERGENS,
        user_diets=USER_DIETS
    )
    
    # Third case: product with scoring algorithm only (no AI)
    logger.info("CASE 3: Analyzing product with algorithm-based scoring (no AI)")
    product_for_algorithm = SAMPLE_PRODUCT.copy()
    if "score" in product_for_algorithm:
        del product_for_algorithm["score"]
    
    # Log detailed calculation steps before using the scoring engine
    logger.info("=== DETAILED SCORING CALCULATION ===")
    log_detailed_score_calculation(product_for_algorithm)
    
    result3 = analyzer.analyze_product(
        product_info=product_for_algorithm,
        user_allergens=USER_ALLERGENS,
        user_diets=USER_DIETS,
        use_ai_scoring=False
    )
    
    # Print results
    logger.info("=== CASE 1 RESULTS (AI-Generated Score with guided JSON) ===")
    print_analysis_results(result1)
    
    logger.info("=== CASE 2 RESULTS (External Score) ===")
    print_analysis_results(result2)
    
    logger.info("=== CASE 3 RESULTS (Algorithm-Based Score) ===")
    print_analysis_results(result3)
    
    logger.info("Example completed")


def log_detailed_score_calculation(product_data):
    """Log detailed steps of the scoring calculation process."""
    # Create a copy of the data for scoring
    scoring_data = product_data.copy()
    
    # Log nutrition values and their scores
    nutrition = scoring_data.get("nutrition", {})
    logger.info("Nutrition Component Scoring (60% of total):")
    
    # Protein scoring
    protein = nutrition.get("protein", 0)
    protein_score = 0
    if protein >= ScoringEngine.PROTEIN_THRESHOLDS["high"]:
        protein_score = 10.0
        protein_rating = "high"
    elif protein >= ScoringEngine.PROTEIN_THRESHOLDS["medium"]:
        protein_score = 5.0
        protein_rating = "medium"
    else:
        protein_rating = "low"
    logger.info(f"  - Protein: {protein}g ({protein_rating}, score: {protein_score}) - Weight: {ScoringEngine.NUTRITION_WEIGHTS['proteins']}")
    
    # Fat scoring
    total_fat = nutrition.get("fat", {}).get("total", 0)
    saturated_fat = nutrition.get("fat", {}).get("saturated", 0)
    fat_score = 0
    if saturated_fat <= ScoringEngine.SATURATED_FAT_THRESHOLDS["medium"]:
        fat_score = 10.0
        fat_rating = "low"
    elif saturated_fat <= ScoringEngine.SATURATED_FAT_THRESHOLDS["high"]:
        fat_score = 5.0
        fat_rating = "medium"
    else:
        fat_rating = "high"
    logger.info(f"  - Fat: {total_fat}g total, {saturated_fat}g saturated ({fat_rating}, score: {fat_score}) - Weight: {ScoringEngine.NUTRITION_WEIGHTS['fats']}")
    
    # Carbs/Sugar scoring
    total_carbs = nutrition.get("carbohydrates", {}).get("total", 0)
    sugar = nutrition.get("carbohydrates", {}).get("sugar", 0)
    carbs_score = 0
    if sugar <= ScoringEngine.SUGAR_THRESHOLDS["medium"]:
        carbs_score = 10.0
        sugar_rating = "low"
    elif sugar <= ScoringEngine.SUGAR_THRESHOLDS["high"]:
        carbs_score = 5.0
        sugar_rating = "medium"
    else:
        sugar_rating = "high"
    logger.info(f"  - Carbs: {total_carbs}g total, {sugar}g sugar ({sugar_rating}, score: {carbs_score}) - Weight: {ScoringEngine.NUTRITION_WEIGHTS['carbs']}")
    
    # Fiber scoring
    fiber = nutrition.get("fiber", 0)
    fiber_score = 0
    if fiber >= ScoringEngine.FIBER_THRESHOLDS["high"]:
        fiber_score = 10.0
        fiber_rating = "high"
    elif fiber >= ScoringEngine.FIBER_THRESHOLDS["medium"]:
        fiber_score = 5.0
        fiber_rating = "medium"
    else:
        fiber_rating = "low"
    logger.info(f"  - Fiber: {fiber}g ({fiber_rating}, score: {fiber_score}) - Weight: {ScoringEngine.NUTRITION_WEIGHTS['fiber']}")
    
    # Salt scoring
    salt = nutrition.get("salt", 0)
    salt_score = 0
    if salt <= ScoringEngine.SALT_THRESHOLDS["medium"]:
        salt_score = 10.0
        salt_rating = "low"
    elif salt <= ScoringEngine.SALT_THRESHOLDS["high"]:
        salt_score = 5.0
        salt_rating = "medium"
    else:
        salt_rating = "high"
    logger.info(f"  - Salt: {salt}g ({salt_rating}, score: {salt_score}) - Weight: {ScoringEngine.NUTRITION_WEIGHTS['salt']}")
    
    # Calories scoring
    calories = nutrition.get("calories", 0)
    calories_score = 0
    if calories <= ScoringEngine.CALORIE_THRESHOLDS["medium"]:
        calories_score = 10.0
        calories_rating = "low"
    elif calories <= ScoringEngine.CALORIE_THRESHOLDS["high"]:
        calories_score = 5.0
        calories_rating = "medium"
    else:
        calories_rating = "high"
    logger.info(f"  - Calories: {calories} kcal ({calories_rating}, score: {calories_score}) - Weight: {ScoringEngine.NUTRITION_WEIGHTS['calories']}")
    
    # Calculate weighted nutrition score
    nutrition_weights = ScoringEngine.NUTRITION_WEIGHTS
    weighted_nutrition_score = (
        protein_score * nutrition_weights["proteins"] +
        fat_score * nutrition_weights["fats"] +
        carbs_score * nutrition_weights["carbs"] +
        fiber_score * nutrition_weights["fiber"] +
        salt_score * nutrition_weights["salt"] +
        calories_score * nutrition_weights["calories"]
    )
    nutrition_score = weighted_nutrition_score * 10
    logger.info(f"  = Nutrition Score: {nutrition_score:.1f}/100")
    
    # Additives scoring (40% of total)
    logger.info("Additives Component Scoring (40% of total):")
    
    # Extract additives from product data
    additives = scoring_data.get("additives", [])
    ingredients = scoring_data.get("ingredients", [])
    
    # Get reference lists
    safe_additives = set(scoring_data.get("safe_additives", []))
    suspicious_additives = set(scoring_data.get("suspicious_additives", []))
    harmful_additives = set(scoring_data.get("harmful_additives", []))
    
    # Log all additives being evaluated
    logger.info(f"  - Additives found: {additives}")
    logger.info(f"  - Safe additives reference: {', '.join(list(safe_additives)[:5])}...")
    logger.info(f"  - Suspicious additives reference: {', '.join(list(suspicious_additives)[:5])}...")
    logger.info(f"  - Harmful additives reference: {', '.join(list(harmful_additives)[:5])}...")
    
    # Calculate additives scores
    all_additives = set(additives)
    
    # Check for presence of additives in each category
    safe_intersection = safe_additives.intersection(all_additives)
    suspicious_intersection = suspicious_additives.intersection(all_additives)
    harmful_intersection = harmful_additives.intersection(all_additives)
    
    # Score for safe additives
    safe_score = 0
    if not all_additives:
        safe_score = 5.0  # Neutral if no additives
        safe_reason = "no additives present (neutral)"
    elif all_additives.issubset(safe_additives):
        safe_score = 10.0  # Only beneficial additives
        safe_reason = "all additives are safe"
    elif safe_intersection:
        safe_score = 5.0  # Some safe additives
        safe_reason = "some safe additives present"
    else:
        safe_reason = "no safe additives present"
    
    logger.info(f"  - Safe additives score: {safe_score} ({safe_reason}) - Weight: {ScoringEngine.ADDITIVES_WEIGHTS['safe']}")
    
    # Score for suspicious additives
    suspicious_score = 0
    if not all_additives:
        suspicious_score = 5.0  # Neutral if no additives
        suspicious_reason = "no additives present (neutral)"
    elif not suspicious_intersection:
        suspicious_score = 10.0  # No suspicious additives
        suspicious_reason = "no suspicious additives present"
    else:
        suspicious_reason = f"contains suspicious additives: {', '.join(suspicious_intersection)}"
    
    logger.info(f"  - Suspicious additives score: {suspicious_score} ({suspicious_reason}) - Weight: {ScoringEngine.ADDITIVES_WEIGHTS['suspicious']}")
    
    # Score for harmful additives
    harmful_score = 0
    if not all_additives:
        harmful_score = 5.0  # Neutral if no additives
        harmful_reason = "no additives present (neutral)"
    elif not harmful_intersection:
        harmful_score = 10.0  # No harmful additives
        harmful_reason = "no harmful additives present"
    else:
        harmful_reason = f"contains harmful additives: {', '.join(harmful_intersection)}"
    
    logger.info(f"  - Harmful additives score: {harmful_score} ({harmful_reason}) - Weight: {ScoringEngine.ADDITIVES_WEIGHTS['harmful']}")
    
    # Calculate weighted additives score
    additives_weights = ScoringEngine.ADDITIVES_WEIGHTS
    weighted_additives_score = (
        safe_score * additives_weights["safe"] +
        suspicious_score * additives_weights["suspicious"] +
        harmful_score * additives_weights["harmful"]
    )
    additives_score = weighted_additives_score * 10
    logger.info(f"  = Additives Score: {additives_score:.1f}/100")
    
    # Calculate final score
    overall_weights = ScoringEngine.OVERALL_WEIGHTS
    final_score = round(
        (nutrition_score * overall_weights["nutrition"]) +
        (additives_score * overall_weights["additives"])
    )
    
    # Get category
    category = ScoringEngine.get_score_category(final_score)
    
    logger.info("Final Score Calculation:")
    logger.info(f"  - Nutrition ({overall_weights['nutrition'] * 100}%): {nutrition_score:.1f}")
    logger.info(f"  - Additives ({overall_weights['additives'] * 100}%): {additives_score:.1f}")
    logger.info(f"  = Total Score: {final_score}/100 (Category: {category})")


def print_analysis_results(analysis):
    """Print analysis results in a readable format."""
    # Product score
    logger.info(f"Product: {analysis.product.name}")
    logger.info(f"Score: {analysis.product.score.total} ({analysis.product.score.category})")
    logger.info(f"  - Nutrition score: {analysis.product.score.nutrition_score}")
    logger.info(f"  - Additives score: {analysis.product.score.additives_score}")
    
    # Allergens
    logger.info("Detected allergens:")
    for allergen in analysis.allergens_analysis.detected_allergens:
        logger.info(f"  - {allergen}")
    
    logger.info("User allergens present:")
    for allergen in analysis.allergens_analysis.user_allergens_present:
        logger.info(f"  - {allergen}")
    
    # Diet compatibility
    logger.info("Diet compatibility:")
    for diet in analysis.diet_compatibility:
        status = "✓ Compatible" if diet.compatible else "✗ Not compatible"
        logger.info(f"  - {diet.diet}: {status}")
        logger.info(f"    Reason: {diet.reason}")


if __name__ == "__main__":
    main() 