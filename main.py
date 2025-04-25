"""
WeCare main application entry point.
Runs the complete food product analysis pipeline.
"""
import json
import os
import sys
import argparse
from typing import Dict, Any, Optional

from wecare.utils.logger import setup_logging, get_logger
from wecare.services.ai_service.product_analyzer import ProductAnalyzer
from wecare.config import settings

setup_logging()
logger = get_logger(__name__)


def load_sample_product(product_file: Optional[str] = None) -> Dict[str, Any]:
    """Load a sample product from a JSON file."""
    if product_file and os.path.exists(product_file):
        file_path = product_file
    else:
        # Use default sample product
        sample_files = [f for f in os.listdir('.') if f.endswith('.json') and f[0].isdigit()]
        if not sample_files:
            logger.error("No sample product files found")
            sys.exit(1)
        file_path = sample_files[0]
        logger.info(f"Using sample product: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    product_data = {}
    
    if "product" in data:
        product_data["product"] = data["product"]
        for field in ["code", "id"]:
            if field in data and field not in product_data:
                product_data[field] = data[field]
    else:
        product_data = data
    
    if "safe_additives" not in product_data:
        product_data["safe_additives"] = ["E300", "E306", "E330"]
    if "suspicious_additives" not in product_data:
        product_data["suspicious_additives"] = ["E102", "E104"]
    if "harmful_additives" not in product_data:
        product_data["harmful_additives"] = ["E211", "E250"]
    
    if "nutrition" not in product_data and "product" in product_data and "nutriments" in product_data["product"]:
        nutriments = product_data["product"]["nutriments"]
        product_data["nutrition"] = {
            "calories": nutriments.get("energy-kcal_100g", 0),
            "protein": nutriments.get("proteins_100g", 0),
            "fat": {
                "total": nutriments.get("fat_100g", 0),
                "saturated": nutriments.get("saturated-fat_100g", 0)
            },
            "carbohydrates": {
                "total": nutriments.get("carbohydrates_100g", 0),
                "sugar": nutriments.get("sugars_100g", 0)
            },
            "fiber": nutriments.get("fiber_100g", 0),
            "salt": nutriments.get("salt_100g", 0),
            "sodium": nutriments.get("sodium_100g", 0)
        }
    
    if "additives" not in product_data and "product" in product_data and "additives_tags" in product_data["product"]:
        product_data["additives"] = [
            additive.replace("en:", "").upper() 
            for additive in product_data["product"]["additives_tags"]
        ]
    
    return product_data


def format_diet_compatibility(analysis):
    """Format diet compatibility results for display."""
    result = []
    for diet in analysis.diet_compatibility:
        status = "✅ Compatible" if diet.compatible else "❌ Not Compatible"
        result.append(f"{diet.diet}: {status}\n  Reason: {diet.reason}")
    return "\n".join(result)


def format_allergen_info(analysis):
    """Format allergen information for display."""
    if not analysis.allergens_analysis.detected_allergens:
        return "No allergens detected"
    
    result = ["Detected allergens:"]
    for allergen in analysis.allergens_analysis.detected_allergens:
        alert = "⚠️ " if allergen in analysis.allergens_analysis.user_allergens_present else "  "
        result.append(f"{alert}{allergen}")
    
    if analysis.allergens_analysis.user_allergens_present:
        result.append("\n⚠️ WARNING: Product contains allergens you're sensitive to!")
    
    return "\n".join(result)


def display_results(analysis, scoring_method_used, product_data=None):
    """Display product analysis results."""
    product = analysis.product
    
    print("\n" + "="*80)
    print(f"PRODUCT ANALYSIS: {product.name}")
    print("="*80)
    
    # Basic product info
    print(f"\nProduct ID: {product.barcode}")
    print(f"Manufacturer: {product.manufacturer}")
    print(f"Weight: {product.weight.value} {product.weight.unit}")
    
    # Score information
    if product.score:
        print(f"\nQUALITY SCORE: {product.score.total}/100 - {product.score.category}")
        print(f"Nutrition Score: {product.score.nutrition_score}/100")
        print(f"Additives Score: {product.score.additives_score}/100")
        print(f"Scoring Method: {scoring_method_used}")
        
        # Add score calculation details
        print("\nSCORE CALCULATION DETAILS:")
        print("---------------------------")
        print("Total Score Formula:")
        print("  (Nutrition Score × 0.6) + (Additives Score × 0.4)")
        print(f"  ({product.score.nutrition_score} × 0.6) + ({product.score.additives_score} × 0.4) = {product.score.total}")
        
        # Access the actual nutrition data from the product
        nutrition = product.nutrition
        
        print("\nNutrition Score Calculation:")
        print(f"  Actual values for {product.name}:")
        print(f"  - Protein: {nutrition.protein}g/100g → {5 if 2.5 <= nutrition.protein < 5 else (10 if nutrition.protein >= 5 else 0)} points")
        print(f"  - Fats: Total {nutrition.fat.total}g, Saturated {nutrition.fat.saturated}g → {5 if 5 <= nutrition.fat.total < 17.5 else (0 if nutrition.fat.total >= 17.5 else 10)} points")
        print(f"  - Carbs: Total {nutrition.carbohydrates.total}g, Sugar {nutrition.carbohydrates.sugar}g → {5 if 5 <= nutrition.carbohydrates.sugar < 22.5 else (0 if nutrition.carbohydrates.sugar >= 22.5 else 10)} points")
        print(f"  - Fiber: {nutrition.fiber}g/100g → {5 if 3 <= nutrition.fiber < 6 else (10 if nutrition.fiber >= 6 else 0)} points")
        print(f"  - Salt: {nutrition.salt}g/100g → {5 if 0.3 <= nutrition.salt < 1.5 else (0 if nutrition.salt >= 1.5 else 10)} points")
        print(f"  - Calories: {nutrition.calories}kcal/100g → {5 if 200 <= nutrition.calories < 400 else (0 if nutrition.calories >= 400 else 10)} points")
        
        # Calculate the estimated component points based on usual thresholds
        protein_points = 5 if 2.5 <= nutrition.protein < 5 else (10 if nutrition.protein >= 5 else 0)
        fat_points = 5 if 5 <= nutrition.fat.total < 17.5 else (0 if nutrition.fat.total >= 17.5 else 10)
        carb_points = 5 if 5 <= nutrition.carbohydrates.sugar < 22.5 else (0 if nutrition.carbohydrates.sugar >= 22.5 else 10)
        fiber_points = 5 if 3 <= nutrition.fiber < 6 else (10 if nutrition.fiber >= 6 else 0)
        salt_points = 5 if 0.3 <= nutrition.salt < 1.5 else (0 if nutrition.salt >= 1.5 else 10)
        calorie_points = 5 if 200 <= nutrition.calories < 400 else (0 if nutrition.calories >= 400 else 10)
        
        # Calculate the estimated score
        estimated_score = ((protein_points * 0.2) + (fat_points * 0.2) + 
                          (carb_points * 0.2) + (fiber_points * 0.1) + 
                          (salt_points * 0.1) + (calorie_points * 0.2)) * 10
        
        print(f"\n  Calculated breakdown (estimated):")
        print(f"  (({protein_points}×0.2) + ({fat_points}×0.2) + ({carb_points}×0.2) + ({fiber_points}×0.1) + ({salt_points}×0.1) + ({calorie_points}×0.2)) × 10")
        print(f"  = ({protein_points * 0.2 + fat_points * 0.2 + carb_points * 0.2 + fiber_points * 0.1 + salt_points * 0.1 + calorie_points * 0.2}) × 10")
        print(f"  = {estimated_score:.1f} ≈ {round(estimated_score)}")
        
        print("\nAdditives Score Calculation:")
        # Get additives from product
        additives = product.additives
        print(f"  Additives found in {product.name}:")
        
        # Display all additives with their safety classification
        if additives:
            for additive in additives:
                safety = "Safe"  # Default classification
                if product_data and additive in product_data.get("harmful_additives", []):
                    safety = "Harmful"
                elif product_data and additive in product_data.get("suspicious_additives", []):
                    safety = "Suspicious"
                print(f"  - {additive}: {safety}")
        else:
            print("  - No additives found in this product")
        
        # Calculate safe, suspicious, harmful percentages
        safe_additives = [] if not product_data else product_data.get("suspicious_additives", [])
        suspicious_additives = [] if not product_data else product_data.get("suspicious_additives", [])
        harmful_additives = [] if not product_data else product_data.get("harmful_additives", [])
        
        safe_count = sum(1 for a in additives if a not in suspicious_additives and a not in harmful_additives)
        suspicious_count = sum(1 for a in additives if a in suspicious_additives)
        harmful_count = sum(1 for a in additives if a in harmful_additives)
        total_additives = max(1, len(additives))  # Avoid division by zero
        
        # Calculate the points (0-10 scale)
        safe_points = 10 if safe_count == total_additives else (5 if safe_count > 0 else 0)
        suspicious_points = 0 if suspicious_count > 0 else 10
        harmful_points = 0 if harmful_count > 0 else 10
        
        # Calculate the weighted score
        additives_calc = (safe_points * 0.4) + (suspicious_points * 0.3) + (harmful_points * 0.3)
        estimated_additives_score = additives_calc * 10
        
        print(f"\n  Additives score breakdown:")
        print(f"  - Safe additives: {safe_count}/{total_additives} → {safe_points} points (40% weight)")
        print(f"  - Suspicious additives: {suspicious_count}/{total_additives} → {suspicious_points} points (30% weight)")
        print(f"  - Harmful additives: {harmful_count}/{total_additives} → {harmful_points} points (30% weight)")
        print(f"  Formula: ({safe_points}×0.4 + {suspicious_points}×0.3 + {harmful_points}×0.3) × 10 = {estimated_additives_score}")
    else:
        print("\nQUALITY SCORE: Not available")
    
    # Allergen information
    print("\nALLERGEN INFORMATION:")
    print(format_allergen_info(analysis))
    
    # Diet compatibility
    print("\nDIET COMPATIBILITY:")
    print(format_diet_compatibility(analysis))
    
    print("\n" + "="*80)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="WeCare Product Analysis Tool")
    
    parser.add_argument(
        "product_file", 
        nargs="?", 
        help="Path to a product JSON file"
    )
    
    parser.add_argument(
        "--scoring", 
        choices=["ai", "local", "external", "auto"],
        default="auto",
        help="Scoring method to use: ai=AI-based scoring, local=Local scoring engine, external=Use external score if available, auto=Best available method (default)"
    )
    
    parser.add_argument(
        "--allergens",
        nargs="+",
        default=["Peanuts", "Shellfish", "Gluten"],
        help="List of user allergens to check"
    )
    
    parser.add_argument(
        "--diets",
        nargs="+",
        default=["Vegetarian", "Low-Sugar"],
        help="List of dietary preferences to check"
    )
    
    return parser.parse_args()


def main():
    """Run the main application pipeline."""
    try:
        logger.info("Starting WeCare product analysis pipeline")
        
        args = parse_args()
        
        use_ai_scoring = args.scoring in ["ai", "auto"]
        scoring_method_used = "Not determined yet"
        
        product_data = load_sample_product(args.product_file)
        product_name = product_data.get("product", {}).get("product_name", "Unknown")
        logger.info(f"Loaded product: {product_name}")
        
        api_key = os.environ.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        analyzer = ProductAnalyzer(api_key=api_key)
        logger.info("Initialized product analyzer")
        
        has_external_score = "score" in product_data and product_data.get("score") is not None
        
        # Determine the actual scoring method based on arguments and data availability
        if args.scoring == "external" or (args.scoring == "auto" and has_external_score):
            # Force use of external score if available
            if has_external_score:
                use_ai_scoring = False
                scoring_method_used = "External Score (provided with product data)"
            else:
                logger.warning("External score requested but not available. Using local scoring instead.")
                use_ai_scoring = False
                scoring_method_used = "Local Scoring Engine (fallback from external)"
        elif args.scoring == "local":
            use_ai_scoring = False
            scoring_method_used = "Local Scoring Engine"
        elif args.scoring == "ai":
            use_ai_scoring = True
            scoring_method_used = "AI-Generated Score (requested)"
        else:  # auto
            scoring_method_used = "Automatic Selection"
        
        # Analyze product
        result = analyzer.analyze_product(
            product_info=product_data,
            user_allergens=args.allergens,
            user_diets=args.diets,
            use_ai_scoring=use_ai_scoring
        )
        logger.info("Product analysis completed successfully")
        
        # Check if fallback analysis was used (which indicates AI failed)
        ai_failed = all(not diet.compatible and "Unable to determine" in diet.reason 
                       for diet in result.diet_compatibility)
        
        # Update the scoring method used based on the actual result
        if has_external_score and scoring_method_used == "Automatic Selection":
            scoring_method_used = "External Score (provided with product data)"
        elif "AI-Generated" in scoring_method_used and ai_failed:
            # AI was requested but failed
            scoring_method_used = "Local Scoring Engine (fallback from AI error)"
        elif scoring_method_used in ["Automatic Selection", "AI-Generated Score (requested)"] and result.product.score:
            if use_ai_scoring and not ai_failed:
                scoring_method_used = "AI-Generated Score"
            else:
                scoring_method_used = "Local Scoring Engine"
        
        # Display results
        display_results(result, scoring_method_used, product_data)
        
        return 0
    except Exception as e:
        logger.error(f"Error in WeCare pipeline: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
