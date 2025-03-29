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

## Project Structure
- `app.py`: Main application file with GUI components
- `models.py`: Data models for drugs, ingredients, and effects
- `requirements.txt`: Dependencies

## Features Implemented
1. **Drug Management**
   - Add, edit, and delete drugs
   - View drug details including ingredients and effects
   - Calculate costs and profit margins

2. **Ingredient Management**
   - Add, edit, and delete ingredients
   - Track ingredient costs
   - Select ingredients from dropdown when adding to drugs

3. **Effect Management**
   - Add, edit, and delete effects
   - Assign custom colors to effects
   - Select effects from dropdown when adding to drugs
   - Color picker for visual identification of effects

4. **Data Persistence**
   - Save/load functionality for drugs, ingredients, and effects
   - JSON file format for data storage

## Recent Changes
- Removed potency attribute from effects as it's not part of the game
- Added color picker for effects to allow visual customization
- Updated UI to display effect colors in tables and details views

## Technical Notes
- Using PyQt5 for the GUI
- Data is stored in separate JSON files for drugs, ingredients, and effects
- Color values are stored as hex strings (e.g., "#FF0000" for red)

## Future Improvements
- Color-coded visualization for effects in drug details view
- Sorting and filtering options
- Export functionality for reports
- Batch processing for multiple drugs
