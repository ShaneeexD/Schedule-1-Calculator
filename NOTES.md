# Development Notes

## Project Overview
This tool is designed for the game "Schedule 1" to help players manage drug recipes and calculate costs efficiently. Based on the game screenshot, players need to track various drugs, their ingredients, effects, and pricing.

## Game Analysis
From the screenshot, we can observe:
- The game has a "Product Manager" interface
- Drugs have various attributes including price, effects, and ingredients
- There appears to be a favorites system
- Each drug has multiple possible ingredients/variants

## Technical Approach
1. Create a PyQt5-based GUI application
2. Implement a data structure to store drugs and their properties
3. Create a database (JSON-based for simplicity) to persist user data
4. Implement calculation logic for pricing based on ingredients

## Data Structure
```
Drug:
  - name: string
  - base_price: float
  - ingredients: list of Ingredient objects
  - effects: list of strings (optional)

Ingredient:
  - name: string
  - quantity: int
  - unit_price: float
```

## Implementation Plan
1. Set up the basic project structure
2. Create the main GUI window with PyQt5
3. Implement the "Add Drug" functionality
4. Create the ingredients management system
5. Implement cost calculation logic
6. Add save/load functionality
7. Enhance with additional features (effects, favorites) if time permits
