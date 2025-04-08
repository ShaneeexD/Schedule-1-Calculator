"""
Models for the Schedule 1 Drug Recipe Calculator
"""
from typing import List, Dict, Optional
import json
from dataclasses import dataclass, asdict


@dataclass
class Ingredient:
    """Represents an ingredient in a drug recipe"""
    name: str
    quantity: float
    unit_price: float

    @property
    def total_cost(self) -> float:
        """Calculate the total cost of this ingredient"""
        return self.quantity * self.unit_price


@dataclass
class Effect:
    """Represents an effect that a drug can have"""
    name: str
    description: str = ""
    color: str = "#FFFFFF"  # Default color is white


@dataclass
class Drug:
    """Represents a drug with its recipe and pricing information"""
    name: str
    base_price: float
    ingredients: List[Ingredient]
    effects: List[Effect] = None
    notes: str = ""
    drug_type: str = "Weed"  # Default type is Weed, other options are Meth and Cocaine

    def __post_init__(self):
        """Initialize default values"""
        if self.effects is None:
            self.effects = []

    @property
    def ingredient_cost(self) -> float:
        """Calculate the total cost of all ingredients"""
        return sum(ingredient.total_cost for ingredient in self.ingredients)

    @property
    def profit_margin(self) -> float:
        """Calculate the profit margin percentage"""
        if self.ingredient_cost == 0:
            return 0
        return ((self.base_price - self.ingredient_cost) / self.ingredient_cost) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
        
    def to_firebase_dict(self) -> Dict:
        """Convert to dictionary format suitable for Firebase"""
        # Create a base dictionary with drug properties
        result = {
            "name": self.name,
            "base_price": self.base_price,
            "notes": self.notes,
            "ingredient_cost": self.ingredient_cost,
            "profit_margin": self.profit_margin,
            "drug_type": self.drug_type
        }
        
        # Add ingredients
        result["ingredients"] = []
        for ingredient in self.ingredients:
            result["ingredients"].append({
                "name": ingredient.name,
                "quantity": ingredient.quantity,
                "unit_price": ingredient.unit_price,
                "total_cost": ingredient.total_cost
            })
        
        # Add effects
        result["effects"] = []
        for effect in self.effects:
            result["effects"].append({
                "name": effect.name,
                "description": effect.description,
                "color": effect.color
            })
            
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'Drug':
        """Create a Drug instance from a dictionary"""
        ingredients = [Ingredient(**ing) for ing in data.pop('ingredients', [])]
        effects_data = data.pop('effects', [])
        effects = []
        
        # Handle effects with backward compatibility
        for effect_data in effects_data:
            # Convert old format (with potency) to new format (with color)
            if 'potency' in effect_data and 'color' not in effect_data:
                # Use a default color based on potency value (1-10)
                potency = effect_data.pop('potency', 5)
                # Generate a color from blue (potency 1) to red (potency 10)
                # This creates a gradient of colors based on the old potency value
                intensity = min(255, int((potency / 10) * 255))
                color = f"#{255-intensity:02x}{0:02x}{intensity:02x}"
                effect_data['color'] = color
            
            effects.append(Effect(**effect_data))
            
        return cls(ingredients=ingredients, effects=effects, **data)
        
    @classmethod
    def from_firebase_dict(cls, data: Dict) -> 'Drug':
        """Create a Drug instance from a Firebase dictionary"""
        # Extract basic properties
        name = data.get("name", "")
        base_price = data.get("base_price", 0.0)
        notes = data.get("notes", "")
        drug_type = data.get("drug_type", "Weed")  # Default to Weed if not specified
        
        # Extract ingredients
        ingredients = []
        for ing_data in data.get("ingredients", []):
            ingredients.append(Ingredient(
                name=ing_data.get("name", ""),
                quantity=ing_data.get("quantity", 1.0),
                unit_price=ing_data.get("unit_price", 0.0)
            ))
        
        # Extract effects
        effects = []
        for effect_data in data.get("effects", []):
            effects.append(Effect(
                name=effect_data.get("name", ""),
                description=effect_data.get("description", ""),
                color=effect_data.get("color", "#FFFFFF")
            ))
        
        return cls(name=name, base_price=base_price, ingredients=ingredients, effects=effects, notes=notes, drug_type=drug_type)


class EffectDatabase:
    """Manages a collection of effects"""
    def __init__(self):
        # Initialize with hard-coded effects data
        self.effects: List[Effect] = [
            Effect(name="Explosive", description="", color="#ff0000"),
            Effect(name="Electrifying", description="", color="#00ffff"),
            Effect(name="Glowing", description="", color="#1aff22"),
            Effect(name="Tropic Thunder", description="", color="#ff8000"),
            Effect(name="Zombifying", description="", color="#008d00"),
            Effect(name="Cyclopean", description="", color="#ff8000"),
            Effect(name="Bright-Eyed", description="", color="#aaffff"),
            Effect(name="Long Faced", description="", color="#b9b95c"),
            Effect(name="Foggy", description="", color="#969696"),
            Effect(name="Anti-Gravity", description="", color="#0800ff"),
            Effect(name="Balding", description="", color="#e89300"),
            Effect(name="Thought-Provoking", description="", color="#ffaaff"),
            Effect(name="Sedating", description="", color="#55557f"),
            Effect(name="Smelly", description="", color="#55aa00"),
            Effect(name="Toxic", description="", color="#499100"),
            Effect(name="Calorie-Dense", description="", color="#ffaaff"),
            Effect(name="Athletic", description="", color="#00ffff"),
            Effect(name="Slippery", description="", color="#aaffff"),
            Effect(name="Gingeritis", description="", color="#ff8000"),
            Effect(name="Spicy", description="", color="#ff4c3c"),
            Effect(name="Seizure-Inducing", description="", color="#b9b95c"),
            Effect(name="Schizophrenia", description="", color="#5555ff"),
            Effect(name="Jennerising", description="", color="#ffaaff"),
            Effect(name="Sneaky", description="", color="#969696"),
            Effect(name="Refreshing", description="", color="#22aa61"),
            Effect(name="Energizing", description="", color="#00aa00"),
            Effect(name="Paranoia", description="", color="#ff4800")
        ]

    def add_effect(self, effect: Effect) -> None:
        """Add an effect to the database"""
        self.effects.append(effect)

    def remove_effect(self, effect_name: str) -> bool:
        """Remove an effect from the database by name"""
        for i, effect in enumerate(self.effects):
            if effect.name == effect_name:
                self.effects.pop(i)
                return True
        return False

    def get_effect(self, effect_name: str) -> Optional[Effect]:
        """Get an effect by name"""
        for effect in self.effects:
            if effect.name == effect_name:
                return effect
        return None
    
    def get_effect_names(self) -> List[str]:
        """Get a list of all effect names"""
        return [effect.name for effect in self.effects]

    # Methods for loading/saving effects from/to JSON files have been removed
    # since effects are now hard-coded


class IngredientDatabase:
    """Manages a collection of base ingredients"""
    def __init__(self):
        # Initialize with hard-coded ingredients data
        self.ingredients: List[Ingredient] = [
            Ingredient(name="Cuke", quantity=1.0, unit_price=2.0),
            Ingredient(name="Banana", quantity=1.0, unit_price=2.0),
            Ingredient(name="Paracetamol", quantity=1.0, unit_price=3.0),
            Ingredient(name="Donut", quantity=1.0, unit_price=3.0),
            Ingredient(name="Viagra", quantity=1.0, unit_price=4.0),
            Ingredient(name="Mouth Wash", quantity=1.0, unit_price=4.0),
            Ingredient(name="Flu Medicine", quantity=1.0, unit_price=5.0),
            Ingredient(name="Gasoline", quantity=1.0, unit_price=5.0),
            Ingredient(name="Energy Drink", quantity=1.0, unit_price=6.0),
            Ingredient(name="Motor Oil", quantity=1.0, unit_price=6.0),
            Ingredient(name="Mega Bean", quantity=1.0, unit_price=7.0),
            Ingredient(name="Chili", quantity=1.0, unit_price=7.0),
            Ingredient(name="Battery", quantity=1.0, unit_price=8.0),
            Ingredient(name="Iodine", quantity=1.0, unit_price=8.0),
            Ingredient(name="Addy", quantity=1.0, unit_price=9.0),
            Ingredient(name="Horse Semen", quantity=1.0, unit_price=9.0)
        ]

    def add_ingredient(self, ingredient: Ingredient) -> None:
        """Add an ingredient to the database"""
        self.ingredients.append(ingredient)

    def remove_ingredient(self, ingredient_name: str) -> bool:
        """Remove an ingredient from the database by name"""
        for i, ingredient in enumerate(self.ingredients):
            if ingredient.name == ingredient_name:
                self.ingredients.pop(i)
                return True
        return False

    def get_ingredient(self, ingredient_name: str) -> Optional[Ingredient]:
        """Get an ingredient by name"""
        for ingredient in self.ingredients:
            if ingredient.name == ingredient_name:
                return ingredient
        return None
    
    def get_ingredient_names(self) -> List[str]:
        """Get a list of all ingredient names"""
        return [ingredient.name for ingredient in self.ingredients]

    # Methods for loading/saving ingredients from/to JSON files have been removed
    # since ingredients are now hard-coded


class DrugDatabase:
    """Manages a collection of drugs"""
    def __init__(self):
        self.drugs: List[Drug] = []

    def add_drug(self, drug: Drug) -> None:
        """Add a drug to the database"""
        self.drugs.append(drug)

    def remove_drug(self, drug_name: str) -> bool:
        """Remove a drug from the database by name"""
        for i, drug in enumerate(self.drugs):
            if drug.name == drug_name:
                self.drugs.pop(i)
                return True
        return False

    def get_drug(self, drug_name: str) -> Optional[Drug]:
        """Get a drug by name"""
        for drug in self.drugs:
            if drug.name == drug_name:
                return drug
        return None

    def save_to_file(self, filename: str) -> None:
        """Save the database to a JSON file"""
        with open(filename, 'w') as f:
            json.dump([drug.to_dict() for drug in self.drugs], f, indent=2)

    def load_from_file(self, filename: str) -> None:
        """Load the database from a JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.drugs = [Drug.from_dict(drug_data) for drug_data in data]
        except (FileNotFoundError, json.JSONDecodeError):
            self.drugs = []
