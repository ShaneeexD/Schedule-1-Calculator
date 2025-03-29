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

    @classmethod
    def from_dict(cls, data: Dict) -> 'Drug':
        """Create a Drug instance from a dictionary"""
        ingredients = [Ingredient(**ing) for ing in data.pop('ingredients', [])]
        effects_data = data.pop('effects', [])
        effects = [Effect(**effect) for effect in effects_data] if effects_data else []
        return cls(ingredients=ingredients, effects=effects, **data)


class EffectDatabase:
    """Manages a collection of effects"""
    def __init__(self):
        self.effects: List[Effect] = []

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

    def save_to_file(self, filename: str) -> None:
        """Save the database to a JSON file"""
        with open(filename, 'w') as f:
            json.dump([asdict(effect) for effect in self.effects], f, indent=2)

    def load_from_file(self, filename: str) -> None:
        """Load the database from a JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.effects = [Effect(**effect_data) for effect_data in data]
        except (FileNotFoundError, json.JSONDecodeError):
            self.effects = []


class IngredientDatabase:
    """Manages a collection of base ingredients"""
    def __init__(self):
        self.ingredients: List[Ingredient] = []

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

    def save_to_file(self, filename: str) -> None:
        """Save the database to a JSON file"""
        with open(filename, 'w') as f:
            json.dump([asdict(ingredient) for ingredient in self.ingredients], f, indent=2)

    def load_from_file(self, filename: str) -> None:
        """Load the database from a JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.ingredients = [Ingredient(**ingredient_data) for ingredient_data in data]
        except (FileNotFoundError, json.JSONDecodeError):
            self.ingredients = []


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
