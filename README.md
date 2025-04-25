# WeCare

A nutritional analysis and food scoring application that helps users make informed decisions about the products they consume.

## Project Description

WeCare is a comprehensive food product analysis tool that provides:

- **Nutritional Analysis**: Evaluates the nutritional content of food products against health guidelines
- **Ingredient Safety Assessment**: Analyzes ingredients and additives for potential health concerns
- **Allergen Detection**: Identifies allergens and warns users based on their personal profiles
- **Diet Compatibility**: Evaluates products against various dietary preferences (Vegetarian, Vegan, Keto, etc.)
- **Product Scoring**: Assigns quality scores based on nutritional value and additive content

The application integrates with the Open Food Facts database to retrieve product information and uses both AI-powered analysis and algorithmic scoring to provide users with thorough insights about their food choices.

## Installation

### Prerequisites

- Python 3.10+
- Git

### Installing uv

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. Install it using:

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
irm 'https://astral.sh/uv/install.ps1' | iex
```

Verify the installation:

```bash
uv --version
```

### Installing WeCare

1. Clone the repository:

```bash
git clone https://github.com/AlimKAH/WeCare.git
cd WeCare
```

2. Create a virtual environment and install dependencies using uv:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. Set up environment variables:

```bash
# Linux/macOS
export OPENAI_API_KEY="your-api-key-here"

# Windows
set OPENAI_API_KEY=your-api-key-here
```

## Implementation Details

WeCare is built with a modular architecture focused on maintainability and extensibility:

### Core Components

- **Models**: Data structures defined in `wecare/core/models/schemas.py`
- **Scoring Engine**: Algorithmic scoring system in `wecare/core/scoring/scoring_engine.py`
- **AI Service**: Integration with OpenAI for advanced analysis in `wecare/services/ai_service/`
- **Product Analyzer**: High-level service coordinating the analysis workflow

### Key Design Features

1. **Multifaceted Analysis**:
   - Combines AI-powered insights with rule-based scoring
   - Offers flexibility to use either or both approaches

2. **Robust Fallback Mechanisms**:
   - Hierarchical scoring approach (external → AI → local algorithm)
   - Graceful error handling with meaningful fallbacks

3. **Template-Guided AI Responses**:
   - Uses structured JSON templates to guide AI responses
   - Ensures consistency in analysis results

4. **Open Food Facts Integration**:
   - Parses and standardizes external product data
   - Handles diverse product information formats

## Scoring Engine Explanation

The scoring engine evaluates products on two main dimensions:

### 1. Nutritional Value (60% of total score)

- **Protein (20%)**: Higher protein content receives better scores
  - High: 10 points (≥5g per 100g)
  - Medium: 5 points (≥2.5g per 100g)
  - Low: 0 points (<2.5g per 100g)

- **Fats (20%)**: Lower saturated fat content receives better scores
  - Low: 10 points (≤1.5g per 100g)
  - Medium: 5 points (≤5g per 100g)
  - High: 0 points (>5g per 100g)

- **Carbohydrates (20%)**: Lower sugar content receives better scores
  - Low: 10 points (≤5g per 100g)
  - Medium: 5 points (≤22.5g per 100g)
  - High: 0 points (>22.5g per 100g)

- **Fiber (10%)**: Higher fiber content receives better scores
  - High: 10 points (≥6g per 100g)
  - Medium: 5 points (≥3g per 100g)
  - Low: 0 points (<3g per 100g)

- **Salt (10%)**: Lower salt content receives better scores
  - Low: 10 points (≤0.3g per 100g)
  - Medium: 5 points (≤1.5g per 100g)
  - High: 0 points (>1.5g per 100g)

- **Calories (20%)**: Lower calorie content receives better scores
  - Low: 10 points (≤200 kcal per 100g)
  - Medium: 5 points (≤400 kcal per 100g)
  - High: 0 points (>400 kcal per 100g)

### 2. Additives Evaluation (40% of total score)

- **Safe Additives (40%)**:
  - All additives are safe: 10 points
  - Some safe additives present: 5 points
  - No safe additives: 0 points

- **Suspicious Additives (30%)**:
  - No suspicious additives: 10 points
  - Contains suspicious additives: 0 points

- **Harmful Additives (30%)**:
  - No harmful additives: 10 points
  - Contains harmful additives: 0 points

### Score Categories

The final score determines the product's quality category:

- **81-100**: Excellent (recommended)
- **61-80**: Good (moderately recommended)
- **41-60**: Average (limited recommendation)
- **21-40**: Low Quality (not recommended)
- **0-20**: Very Low Quality (avoid)

## Usage

Run the main application with a product barcode JSON file:

```bash
python main.py <product_file.json>
```

The main application supports several command-line options:

```
usage: main.py [-h] [--scoring {ai,local,external,auto}] [--allergens ALLERGENS [ALLERGENS ...]] [--diets DIETS [DIETS ...]] [product_file]

WeCare Product Analysis Tool

positional arguments:
  product_file          Path to a product JSON file

options:
  -h, --help            show this help message and exit
  --scoring {ai,local,external,auto}
                        Scoring method to use: ai=AI-based scoring, local=Local scoring engine, external=Use external score if available, auto=Best available method (default)
  --allergens ALLERGENS [ALLERGENS ...]
                        List of user allergens to check
  --diets DIETS [DIETS ...]
                        List of dietary preferences to check
```

### Examples

1. **Use AI-based scoring (if available):**
   ```bash
   python main.py --scoring ai
   ```

2. **Use local scoring algorithm only:**
   ```bash
   python main.py --scoring local
   ```

3. **Analyze with custom allergens and diets:**
   ```bash
   python main.py --allergens Peanuts Dairy Gluten --diets Keto LowCarb
   ```

The application provides comprehensive output including:
1. Basic product information
2. Quality score and category
3. Detailed calculation of nutritional and additives scores
4. Allergen detection and warnings
5. Diet compatibility analysis
