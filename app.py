"""
Schedule 1 Drug Recipe Calculator - Main Application
"""
import sys
import os
import json
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
                           QSpinBox, QDoubleSpinBox, QFormLayout, QDialog, QMessageBox,
                           QTabWidget, QFileDialog, QHeaderView, QComboBox, QTextEdit,
                           QColorDialog, QSlider)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor

from models import Drug, Ingredient, DrugDatabase, IngredientDatabase, Effect, EffectDatabase


class IngredientDialog(QDialog):
    """Dialog for adding/editing ingredients"""
    def __init__(self, parent=None, ingredient=None):
        super().__init__(parent)
        self.setWindowTitle("Add Ingredient")
        self.setMinimumWidth(400)
        
        # Initialize with existing ingredient if editing
        self.ingredient = ingredient
        
        # Create form layout
        layout = QFormLayout()
        
        # Ingredient name
        self.name_input = QLineEdit()
        if ingredient:
            self.name_input.setText(ingredient.name)
        layout.addRow("Ingredient Name:", self.name_input)
        
        # Quantity
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.1, 1000)
        self.quantity_input.setSingleStep(0.1)
        self.quantity_input.setDecimals(1)
        if ingredient:
            self.quantity_input.setValue(ingredient.quantity)
        else:
            self.quantity_input.setValue(1.0)
        layout.addRow("Quantity:", self.quantity_input)
        
        # Unit price
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 10000)
        self.price_input.setSingleStep(0.01)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        if ingredient:
            self.price_input.setValue(ingredient.unit_price)
        else:
            self.price_input.setValue(10.0)
        layout.addRow("Unit Price:", self.price_input)
        
        # Total cost (calculated)
        self.total_cost = QLabel("$0.00")
        layout.addRow("Total Cost:", self.total_cost)
        
        # Connect signals to update total cost
        self.quantity_input.valueChanged.connect(self.update_total_cost)
        self.price_input.valueChanged.connect(self.update_total_cost)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
        
        # Initial update
        self.update_total_cost()
    
    def update_total_cost(self):
        """Update the total cost label based on quantity and price"""
        quantity = self.quantity_input.value()
        price = self.price_input.value()
        total = quantity * price
        self.total_cost.setText(f"${total:.2f}")
    
    def get_ingredient(self) -> Ingredient:
        """Return the ingredient with values from the dialog"""
        return Ingredient(
            name=self.name_input.text(),
            quantity=self.quantity_input.value(),
            unit_price=self.price_input.value()
        )


class AddIngredientToDbDialog(QDialog):
    """Dialog for adding a new ingredient to the database"""
    def __init__(self, parent=None, ingredient=None):
        super().__init__(parent)
        self.setWindowTitle("Add Ingredient to Database")
        self.setMinimumWidth(400)
        
        # Initialize with existing ingredient if editing
        self.ingredient = ingredient
        
        # Create form layout
        layout = QFormLayout()
        
        # Ingredient name
        self.name_input = QLineEdit()
        if ingredient:
            self.name_input.setText(ingredient.name)
        layout.addRow("Ingredient Name:", self.name_input)
        
        # Unit price
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 10000)
        self.price_input.setSingleStep(0.01)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        if ingredient:
            self.price_input.setValue(ingredient.unit_price)
        else:
            self.price_input.setValue(10.0)
        layout.addRow("Unit Price:", self.price_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
    
    def get_ingredient(self) -> Ingredient:
        """Return the ingredient with values from the dialog"""
        return Ingredient(
            name=self.name_input.text(),
            quantity=1.0,  # Default quantity, will be adjusted when added to a drug
            unit_price=self.price_input.value()
        )


class AddEffectToDbDialog(QDialog):
    """Dialog for adding a new effect to the database"""
    def __init__(self, parent=None, effect=None):
        super().__init__(parent)
        self.setWindowTitle("Add Effect to Database")
        self.setMinimumWidth(400)
        
        # Initialize with existing effect if editing
        self.effect = effect
        
        # Create form layout
        layout = QFormLayout()
        
        # Effect name
        self.name_input = QLineEdit()
        if effect:
            self.name_input.setText(effect.name)
        layout.addRow("Effect Name:", self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        if effect and effect.description:
            self.description_input.setText(effect.description)
        layout.addRow("Description:", self.description_input)
        
        # Color selection
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid black;")
        self.color_value = QLabel("#FFFFFF")
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.select_color)
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_value)
        color_layout.addWidget(self.color_button)
        
        # Set initial color if editing
        if effect and hasattr(effect, 'color'):
            self.set_color(effect.color)
        else:
            self.current_color = "#FFFFFF"
            
        layout.addRow("Effect Color:", color_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
    
    def select_color(self):
        """Open color dialog and update preview"""
        color = QColorDialog.getColor(QColor(self.current_color), self, "Select Effect Color")
        if color.isValid():
            hex_color = color.name()
            self.set_color(hex_color)
    
    def set_color(self, hex_color):
        """Set the color preview and value"""
        self.current_color = hex_color
        self.color_preview.setStyleSheet(f"background-color: {hex_color}; border: 1px solid black;")
        self.color_value.setText(hex_color)
    
    def get_effect(self) -> Effect:
        """Return the effect with values from the dialog"""
        return Effect(
            name=self.name_input.text(),
            description=self.description_input.toPlainText(),
            color=self.current_color
        )


class SelectEffectDialog(QDialog):
    """Dialog for selecting an effect from the database"""
    def __init__(self, parent=None, effect_db=None):
        super().__init__(parent)
        self.setWindowTitle("Select Effect")
        self.setMinimumWidth(400)
        self.effect_db = effect_db
        
        # Create form layout
        layout = QFormLayout()
        
        # Effect selection
        self.effect_combo = QComboBox()
        if self.effect_db and self.effect_db.effects:
            self.effect_combo.addItems(self.effect_db.get_effect_names())
        layout.addRow("Select Effect:", self.effect_combo)
        
        # Color display (non-editable, shows the color from the database)
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid black;")
        self.color_value = QLabel("#FFFFFF")
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_value)
        
        layout.addRow("Effect Color:", color_layout)
        
        # Description (display only)
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        layout.addRow("Description:", self.description_label)
        
        # Connect signals
        self.effect_combo.currentIndexChanged.connect(self.update_effect_info)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
        
        # Initial update
        self.update_effect_info()
    
    def update_effect_info(self):
        """Update the description and color based on selected effect"""
        if self.effect_db and self.effect_combo.currentText():
            effect = self.effect_db.get_effect(self.effect_combo.currentText())
            if effect:
                if effect.description:
                    self.description_label.setText(effect.description)
                else:
                    self.description_label.setText("")
                
                # Update color preview
                if hasattr(effect, 'color'):
                    self.color_preview.setStyleSheet(f"background-color: {effect.color}; border: 1px solid black;")
                    self.color_value.setText(effect.color)
                else:
                    self.color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid black;")
                    self.color_value.setText("#FFFFFF")
    
    def get_effect(self) -> Optional[Effect]:
        """Return the selected effect"""
        if not self.effect_combo.currentText() or not self.effect_db:
            return None
        
        base_effect = self.effect_db.get_effect(self.effect_combo.currentText())
        if not base_effect:
            return None
        
        return Effect(
            name=base_effect.name,
            description=base_effect.description,
            color=base_effect.color if hasattr(base_effect, 'color') else "#FFFFFF"
        )


class SelectIngredientDialog(QDialog):
    """Dialog for selecting an ingredient from the database and specifying quantity"""
    def __init__(self, parent=None, ingredient_db=None):
        super().__init__(parent)
        self.setWindowTitle("Select Ingredient")
        self.setMinimumWidth(400)
        self.ingredient_db = ingredient_db
        
        # Create form layout
        layout = QFormLayout()
        
        # Ingredient selection
        self.ingredient_combo = QComboBox()
        if self.ingredient_db and self.ingredient_db.ingredients:
            self.ingredient_combo.addItems(self.ingredient_db.get_ingredient_names())
        layout.addRow("Select Ingredient:", self.ingredient_combo)
        
        # Quantity
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.1, 1000)
        self.quantity_input.setSingleStep(0.1)
        self.quantity_input.setDecimals(1)
        self.quantity_input.setValue(1.0)
        layout.addRow("Quantity:", self.quantity_input)
        
        # Unit price (display only)
        self.price_label = QLabel("$0.00")
        layout.addRow("Unit Price:", self.price_label)
        
        # Total cost (calculated)
        self.total_cost = QLabel("$0.00")
        layout.addRow("Total Cost:", self.total_cost)
        
        # Connect signals
        self.ingredient_combo.currentIndexChanged.connect(self.update_price)
        self.quantity_input.valueChanged.connect(self.update_total_cost)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
        
        # Initial update
        self.update_price()
    
    def update_price(self):
        """Update the price label based on selected ingredient"""
        if self.ingredient_db and self.ingredient_combo.currentText():
            ingredient = self.ingredient_db.get_ingredient(self.ingredient_combo.currentText())
            if ingredient:
                self.price_label.setText(f"${ingredient.unit_price:.2f}")
                self.update_total_cost()
    
    def update_total_cost(self):
        """Update the total cost label based on quantity and price"""
        if self.ingredient_db and self.ingredient_combo.currentText():
            ingredient = self.ingredient_db.get_ingredient(self.ingredient_combo.currentText())
            if ingredient:
                quantity = self.quantity_input.value()
                total = quantity * ingredient.unit_price
                self.total_cost.setText(f"${total:.2f}")
    
    def get_ingredient(self) -> Optional[Ingredient]:
        """Return the selected ingredient with specified quantity"""
        if not self.ingredient_combo.currentText() or not self.ingredient_db:
            return None
        
        base_ingredient = self.ingredient_db.get_ingredient(self.ingredient_combo.currentText())
        if not base_ingredient:
            return None
        
        return Ingredient(
            name=base_ingredient.name,
            quantity=self.quantity_input.value(),
            unit_price=base_ingredient.unit_price
        )


class AddDrugDialog(QDialog):
    """Dialog for adding a new drug"""
    def __init__(self, parent=None, drug=None, ingredient_db=None, effect_db=None):
        super().__init__(parent)
        self.setWindowTitle("Add Drug")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Initialize with existing drug if editing
        self.drug = drug
        self.ingredients = []
        self.effects = []
        self.ingredient_db = ingredient_db
        self.effect_db = effect_db
        if drug:
            self.ingredients = drug.ingredients.copy()
            self.effects = drug.effects.copy()
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Form layout for basic info
        form_layout = QFormLayout()
        
        # Drug name
        self.name_input = QLineEdit()
        if drug:
            self.name_input.setText(drug.name)
        form_layout.addRow("Drug Name:", self.name_input)
        
        # Base price
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 100000)
        self.price_input.setSingleStep(1.0)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        if drug:
            self.price_input.setValue(drug.base_price)
        else:
            self.price_input.setValue(100.0)
        form_layout.addRow("Base Price:", self.price_input)
        
        # Notes
        self.notes_input = QTextEdit()
        if drug and drug.notes:
            self.notes_input.setText(drug.notes)
        form_layout.addRow("Notes:", self.notes_input)
        
        main_layout.addLayout(form_layout)
        
        # Ingredients section
        ingredients_label = QLabel("Ingredients:")
        ingredients_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(ingredients_label)
        
        # Ingredients table
        self.ingredients_table = QTableWidget(0, 4)
        self.ingredients_table.setHorizontalHeaderLabels(["Name", "Quantity", "Unit Price", "Total Cost"])
        self.ingredients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        main_layout.addWidget(self.ingredients_table)
        
        # Ingredient buttons
        ing_buttons_layout = QHBoxLayout()
        self.add_ing_button = QPushButton("Add Ingredient")
        self.add_custom_ing_button = QPushButton("Add Custom Ingredient")
        self.edit_ing_button = QPushButton("Edit Ingredient")
        self.remove_ing_button = QPushButton("Remove Ingredient")
        
        self.add_ing_button.clicked.connect(self.add_ingredient)
        self.add_custom_ing_button.clicked.connect(self.add_custom_ingredient)
        self.edit_ing_button.clicked.connect(self.edit_ingredient)
        self.remove_ing_button.clicked.connect(self.remove_ingredient)
        
        ing_buttons_layout.addWidget(self.add_ing_button)
        ing_buttons_layout.addWidget(self.add_custom_ing_button)
        ing_buttons_layout.addWidget(self.edit_ing_button)
        ing_buttons_layout.addWidget(self.remove_ing_button)
        main_layout.addLayout(ing_buttons_layout)
        
        # Effects section
        effects_label = QLabel("Effects:")
        effects_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(effects_label)
        
        # Effects table
        self.effects_table = QTableWidget(0, 3)
        self.effects_table.setHorizontalHeaderLabels(["Name", "Color", "Description"])
        self.effects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        main_layout.addWidget(self.effects_table)
        
        # Effect buttons
        effect_buttons_layout = QHBoxLayout()
        self.add_effect_button = QPushButton("Add Effect")
        self.add_custom_effect_button = QPushButton("Add Custom Effect")
        self.edit_effect_button = QPushButton("Edit Effect")
        self.remove_effect_button = QPushButton("Remove Effect")
        
        self.add_effect_button.clicked.connect(self.add_effect)
        self.add_custom_effect_button.clicked.connect(self.add_custom_effect)
        self.edit_effect_button.clicked.connect(self.edit_effect)
        self.remove_effect_button.clicked.connect(self.remove_effect)
        
        effect_buttons_layout.addWidget(self.add_effect_button)
        effect_buttons_layout.addWidget(self.add_custom_effect_button)
        effect_buttons_layout.addWidget(self.edit_effect_button)
        effect_buttons_layout.addWidget(self.remove_effect_button)
        main_layout.addLayout(effect_buttons_layout)
        
        # Cost summary
        cost_layout = QFormLayout()
        self.total_cost_label = QLabel("$0.00")
        self.profit_margin_label = QLabel("0%")
        cost_layout.addRow("Total Ingredient Cost:", self.total_cost_label)
        cost_layout.addRow("Profit Margin:", self.profit_margin_label)
        main_layout.addLayout(cost_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Populate ingredients if editing
        if drug:
            self.populate_ingredients()
            self.populate_effects()
        
        # Update cost summary
        self.update_cost_summary()
    
    def populate_ingredients(self):
        """Populate the ingredients table with existing ingredients"""
        self.ingredients_table.setRowCount(0)
        for ingredient in self.ingredients:
            self.add_ingredient_to_table(ingredient)
    
    def add_ingredient(self):
        """Open dialog to select an ingredient from the database"""
        if not self.ingredient_db or not self.ingredient_db.ingredients:
            QMessageBox.warning(self, "No Ingredients", 
                               "No ingredients in database. Please add ingredients first.")
            return
            
        dialog = SelectIngredientDialog(self, self.ingredient_db)
        if dialog.exec_():
            ingredient = dialog.get_ingredient()
            if ingredient:
                self.ingredients.append(ingredient)
                self.add_ingredient_to_table(ingredient)
                self.update_cost_summary()
    
    def add_custom_ingredient(self):
        """Open dialog to add a custom ingredient not from the database"""
        dialog = IngredientDialog(self)
        if dialog.exec_():
            ingredient = dialog.get_ingredient()
            self.ingredients.append(ingredient)
            self.add_ingredient_to_table(ingredient)
            self.update_cost_summary()
    
    def edit_ingredient(self):
        """Edit the selected ingredient"""
        selected_row = self.ingredients_table.currentRow()
        if selected_row >= 0:
            ingredient = self.ingredients[selected_row]
            dialog = IngredientDialog(self, ingredient)
            if dialog.exec_():
                self.ingredients[selected_row] = dialog.get_ingredient()
                self.populate_ingredients()
                self.update_cost_summary()
    
    def remove_ingredient(self):
        """Remove the selected ingredient"""
        selected_row = self.ingredients_table.currentRow()
        if selected_row >= 0:
            self.ingredients.pop(selected_row)
            self.ingredients_table.removeRow(selected_row)
            self.update_cost_summary()
    
    def add_ingredient_to_table(self, ingredient: Ingredient):
        """Add an ingredient to the table widget"""
        row = self.ingredients_table.rowCount()
        self.ingredients_table.insertRow(row)
        
        self.ingredients_table.setItem(row, 0, QTableWidgetItem(ingredient.name))
        self.ingredients_table.setItem(row, 1, QTableWidgetItem(f"{ingredient.quantity}"))
        self.ingredients_table.setItem(row, 2, QTableWidgetItem(f"${ingredient.unit_price:.2f}"))
        self.ingredients_table.setItem(row, 3, QTableWidgetItem(f"${ingredient.total_cost:.2f}"))
    
    def populate_effects(self):
        """Populate the effects table with existing effects"""
        self.effects_table.setRowCount(0)
        for effect in self.effects:
            self.add_effect_to_table(effect)
    
    def add_effect(self):
        """Open dialog to select an effect from the database"""
        if not self.effect_db or not self.effect_db.effects:
            QMessageBox.warning(self, "No Effects", 
                               "No effects in database. Please add effects first.")
            return
            
        dialog = SelectEffectDialog(self, self.effect_db)
        if dialog.exec_():
            effect = dialog.get_effect()
            if effect:
                self.effects.append(effect)
                self.add_effect_to_table(effect)
    
    def add_custom_effect(self):
        """Open dialog to add a custom effect not from the database"""
        dialog = AddEffectToDbDialog(self)
        if dialog.exec_():
            effect = dialog.get_effect()
            self.effects.append(effect)
            self.add_effect_to_table(effect)
    
    def edit_effect(self):
        """Edit the selected effect"""
        selected_row = self.effects_table.currentRow()
        if selected_row >= 0:
            effect = self.effects[selected_row]
            dialog = AddEffectToDbDialog(self, effect)
            if dialog.exec_():
                self.effects[selected_row] = dialog.get_effect()
                self.populate_effects()
    
    def remove_effect(self):
        """Remove the selected effect"""
        selected_row = self.effects_table.currentRow()
        if selected_row >= 0:
            self.effects.pop(selected_row)
            self.effects_table.removeRow(selected_row)
    
    def add_effect_to_table(self, effect: Effect):
        """Add an effect to the table widget"""
        row = self.effects_table.rowCount()
        self.effects_table.insertRow(row)
        
        # Create item for effect name with color applied to text
        name_item = QTableWidgetItem(effect.name)
        name_item.setForeground(QColor(effect.color))
        
        self.effects_table.setItem(row, 0, name_item)
        self.effects_table.setItem(row, 1, QTableWidgetItem(effect.color))
        self.effects_table.setItem(row, 2, QTableWidgetItem(effect.description))
    
    def update_cost_summary(self):
        """Update the cost summary labels"""
        total_cost = sum(ing.total_cost for ing in self.ingredients)
        self.total_cost_label.setText(f"${total_cost:.2f}")
        
        base_price = self.price_input.value()
        if total_cost > 0:
            profit_margin = ((base_price - total_cost) / total_cost) * 100
            self.profit_margin_label.setText(f"{profit_margin:.1f}%")
        else:
            self.profit_margin_label.setText("N/A")
    
    def get_drug(self) -> Drug:
        """Return a Drug object with the values from the dialog"""
        return Drug(
            name=self.name_input.text(),
            base_price=self.price_input.value(),
            ingredients=self.ingredients,
            effects=self.effects,
            notes=self.notes_input.toPlainText()
        )


class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule 1 Drug Recipe Calculator")
        self.setMinimumSize(800, 600)
        
        # Initialize database
        self.drug_database = DrugDatabase()
        self.ingredient_database = IngredientDatabase()
        self.effect_database = EffectDatabase()
        self.current_file = None
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Drugs tab
        drugs_tab = QWidget()
        drugs_layout = QVBoxLayout(drugs_tab)
        
        # Drugs table
        self.drugs_table = QTableWidget(0, 5)
        self.drugs_table.setHorizontalHeaderLabels(["Name", "Base Price", "Ingredient Cost", "Profit", "Profit Margin"])
        self.drugs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        drugs_layout.addWidget(self.drugs_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Drug")
        self.edit_button = QPushButton("Edit Drug")
        self.delete_button = QPushButton("Delete Drug")
        self.view_button = QPushButton("View Details")
        
        self.add_button.clicked.connect(self.add_drug)
        self.edit_button.clicked.connect(self.edit_drug)
        self.delete_button.clicked.connect(self.delete_drug)
        self.view_button.clicked.connect(self.view_drug_details)
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.view_button)
        drugs_layout.addLayout(buttons_layout)
        
        # Ingredients tab
        ingredients_tab = QWidget()
        ingredients_layout = QVBoxLayout(ingredients_tab)
        
        # Ingredients table
        self.ingredients_table = QTableWidget(0, 2)
        self.ingredients_table.setHorizontalHeaderLabels(["Name", "Unit Price"])
        self.ingredients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        ingredients_layout.addWidget(self.ingredients_table)
        
        # Ingredient buttons
        ing_buttons_layout = QHBoxLayout()
        self.add_ing_button = QPushButton("Add Ingredient")
        self.edit_ing_button = QPushButton("Edit Ingredient")
        self.delete_ing_button = QPushButton("Delete Ingredient")
        
        self.add_ing_button.clicked.connect(self.add_ingredient_to_db)
        self.edit_ing_button.clicked.connect(self.edit_ingredient_in_db)
        self.delete_ing_button.clicked.connect(self.delete_ingredient_from_db)
        
        ing_buttons_layout.addWidget(self.add_ing_button)
        ing_buttons_layout.addWidget(self.edit_ing_button)
        ing_buttons_layout.addWidget(self.delete_ing_button)
        ingredients_layout.addLayout(ing_buttons_layout)
        
        # Effects tab
        effects_tab = QWidget()
        effects_layout = QVBoxLayout(effects_tab)
        
        # Effects table
        self.effects_table = QTableWidget(0, 2)
        self.effects_table.setHorizontalHeaderLabels(["Name", "Description"])
        self.effects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        effects_layout.addWidget(self.effects_table)
        
        # Effect buttons
        effect_buttons_layout = QHBoxLayout()
        self.add_effect_button = QPushButton("Add Effect")
        self.edit_effect_button = QPushButton("Edit Effect")
        self.delete_effect_button = QPushButton("Delete Effect")
        
        self.add_effect_button.clicked.connect(self.add_effect_to_db)
        self.edit_effect_button.clicked.connect(self.edit_effect_in_db)
        self.delete_effect_button.clicked.connect(self.delete_effect_from_db)
        
        effect_buttons_layout.addWidget(self.add_effect_button)
        effect_buttons_layout.addWidget(self.edit_effect_button)
        effect_buttons_layout.addWidget(self.delete_effect_button)
        effects_layout.addLayout(effect_buttons_layout)
        
        # File operations
        file_buttons_layout = QHBoxLayout()
        self.new_button = QPushButton("New Database")
        self.open_button = QPushButton("Open Database")
        self.save_button = QPushButton("Save")
        self.save_as_button = QPushButton("Save As")
        
        self.new_button.clicked.connect(self.new_database)
        self.open_button.clicked.connect(self.open_database)
        self.save_button.clicked.connect(self.save_database)
        self.save_as_button.clicked.connect(self.save_database_as)
        
        file_buttons_layout.addWidget(self.new_button)
        file_buttons_layout.addWidget(self.open_button)
        file_buttons_layout.addWidget(self.save_button)
        file_buttons_layout.addWidget(self.save_as_button)
        
        # Add file buttons to both tabs
        drugs_layout.addLayout(file_buttons_layout.parentWidget() and QHBoxLayout() or file_buttons_layout)
        ingredients_layout.addLayout(file_buttons_layout)
        effects_layout.addLayout(file_buttons_layout)
        
        # Add tabs
        self.tabs.addTab(drugs_tab, "Drugs")
        self.tabs.addTab(ingredients_tab, "Ingredients")
        self.tabs.addTab(effects_tab, "Effects")
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initialize UI
        self.update_tables()
    
    def add_drug(self):
        """Open dialog to add a new drug"""
        dialog = AddDrugDialog(self, ingredient_db=self.ingredient_database, effect_db=self.effect_database)
        if dialog.exec_():
            drug = dialog.get_drug()
            self.drug_database.add_drug(drug)
            self.update_tables()
            self.statusBar().showMessage(f"Added drug: {drug.name}")
    
    def edit_drug(self):
        """Edit the selected drug"""
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            drug = self.drug_database.drugs[selected_row]
            dialog = AddDrugDialog(self, drug, self.ingredient_database, self.effect_database)
            if dialog.exec_():
                self.drug_database.drugs[selected_row] = dialog.get_drug()
                self.update_tables()
                self.statusBar().showMessage(f"Updated drug: {drug.name}")
    
    def delete_drug(self):
        """Delete the selected drug"""
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            drug = self.drug_database.drugs[selected_row]
            confirm = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete {drug.name}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.drug_database.drugs.pop(selected_row)
                self.update_tables()
                self.statusBar().showMessage(f"Deleted drug: {drug.name}")
    
    def add_ingredient_to_db(self):
        """Add a new ingredient to the database"""
        dialog = AddIngredientToDbDialog(self)
        if dialog.exec_():
            ingredient = dialog.get_ingredient()
            self.ingredient_database.add_ingredient(ingredient)
            self.update_tables()
            self.statusBar().showMessage(f"Added ingredient: {ingredient.name}")
    
    def edit_ingredient_in_db(self):
        """Edit the selected ingredient in the database"""
        selected_row = self.ingredients_table.currentRow()
        if selected_row >= 0:
            ingredient = self.ingredient_database.ingredients[selected_row]
            dialog = AddIngredientToDbDialog(self, ingredient)
            if dialog.exec_():
                new_ingredient = dialog.get_ingredient()
                self.ingredient_database.ingredients[selected_row] = new_ingredient
                self.update_tables()
                self.statusBar().showMessage(f"Updated ingredient: {new_ingredient.name}")
    
    def delete_ingredient_from_db(self):
        """Delete the selected ingredient from the database"""
        selected_row = self.ingredients_table.currentRow()
        if selected_row >= 0:
            ingredient = self.ingredient_database.ingredients[selected_row]
            
            # Check if this ingredient is used in any drugs
            used_in_drugs = []
            for drug in self.drug_database.drugs:
                for ing in drug.ingredients:
                    if ing.name == ingredient.name:
                        used_in_drugs.append(drug.name)
                        break
            
            if used_in_drugs:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"Cannot delete {ingredient.name} because it is used in the following drugs: {', '.join(used_in_drugs)}"
                )
                return
            
            confirm = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete {ingredient.name}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.ingredient_database.ingredients.pop(selected_row)
                self.update_tables()
                self.statusBar().showMessage(f"Deleted ingredient: {ingredient.name}")
    
    def add_effect_to_db(self):
        """Add a new effect to the database"""
        dialog = AddEffectToDbDialog(self)
        if dialog.exec_():
            effect = dialog.get_effect()
            self.effect_database.add_effect(effect)
            self.update_tables()
            self.statusBar().showMessage(f"Added effect: {effect.name}")
    
    def edit_effect_in_db(self):
        """Edit the selected effect in the database"""
        selected_row = self.effects_table.currentRow()
        if selected_row >= 0:
            effect = self.effect_database.effects[selected_row]
            dialog = AddEffectToDbDialog(self, effect)
            if dialog.exec_():
                new_effect = dialog.get_effect()
                self.effect_database.effects[selected_row] = new_effect
                self.update_tables()
                self.statusBar().showMessage(f"Updated effect: {new_effect.name}")
    
    def delete_effect_from_db(self):
        """Delete the selected effect from the database"""
        selected_row = self.effects_table.currentRow()
        if selected_row >= 0:
            effect = self.effect_database.effects[selected_row]
            
            # Check if this effect is used in any drugs
            used_in_drugs = []
            for drug in self.drug_database.drugs:
                for eff in drug.effects:
                    if eff.name == effect.name:
                        used_in_drugs.append(drug.name)
                        break
            
            if used_in_drugs:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"Cannot delete {effect.name} because it is used in the following drugs: {', '.join(used_in_drugs)}"
                )
                return
            
            confirm = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete {effect.name}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.effect_database.effects.pop(selected_row)
                self.update_tables()
                self.statusBar().showMessage(f"Deleted effect: {effect.name}")
    
    def view_drug_details(self):
        """View details of the selected drug"""
        selected_rows = self.drugs_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a drug to view.")
            return
        
        row = selected_rows[0].row()
        drug_name = self.drugs_table.item(row, 0).text()
        drug = self.drug_database.get_drug(drug_name)
        
        if not drug:
            QMessageBox.warning(self, "Error", f"Could not find drug: {drug_name}")
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Drug Details: {drug.name}")
        dialog.setMinimumWidth(600)
        
        # Layout
        layout = QVBoxLayout(dialog)
        
        # Basic info
        info_layout = QFormLayout()
        info_layout.addRow("Name:", QLabel(drug.name))
        info_layout.addRow("Base Price:", QLabel(f"${drug.base_price:.2f}"))
        info_layout.addRow("Ingredient Cost:", QLabel(f"${drug.ingredient_cost:.2f}"))
        info_layout.addRow("Profit:", QLabel(f"${drug.base_price - drug.ingredient_cost:.2f}"))
        info_layout.addRow("Profit Margin:", QLabel(f"{drug.profit_margin:.1f}%"))
        
        if drug.notes:
            notes_label = QLabel(drug.notes)
            notes_label.setWordWrap(True)
            info_layout.addRow("Notes:", notes_label)
        
        layout.addLayout(info_layout)
        
        # Ingredients
        if drug.ingredients:
            ingredients_label = QLabel("Ingredients:")
            ingredients_label.setFont(QFont("Arial", 12, QFont.Bold))
            layout.addWidget(ingredients_label)
            
            ingredients_table = QTableWidget(len(drug.ingredients), 4)
            ingredients_table.setHorizontalHeaderLabels(["Name", "Quantity", "Unit Price", "Total Cost"])
            ingredients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            
            for i, ingredient in enumerate(drug.ingredients):
                ingredients_table.setItem(i, 0, QTableWidgetItem(ingredient.name))
                ingredients_table.setItem(i, 1, QTableWidgetItem(f"{ingredient.quantity}"))
                ingredients_table.setItem(i, 2, QTableWidgetItem(f"${ingredient.unit_price:.2f}"))
                ingredients_table.setItem(i, 3, QTableWidgetItem(f"${ingredient.total_cost:.2f}"))
            
            layout.addWidget(ingredients_table)
        
        # Effects
        if drug.effects:
            effects_label = QLabel("Effects:")
            effects_label.setFont(QFont("Arial", 12, QFont.Bold))
            layout.addWidget(effects_label)
            
            effects_table = QTableWidget(len(drug.effects), 3)
            effects_table.setHorizontalHeaderLabels(["Name", "Color", "Description"])
            effects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            
            for i, effect in enumerate(drug.effects):
                # Create item for effect name with color applied to text
                name_item = QTableWidgetItem(effect.name)
                name_item.setForeground(QColor(effect.color))
                
                effects_table.setItem(i, 0, name_item)
                effects_table.setItem(i, 1, QTableWidgetItem(effect.color))
                effects_table.setItem(i, 2, QTableWidgetItem(effect.description))
            
            layout.addWidget(effects_table)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec_()
    
    def update_tables(self):
        """Update both the drugs and ingredients tables"""
        self.update_drugs_table()
        self.update_ingredients_table()
        self.update_effects_table()
    
    def update_drugs_table(self):
        """Update the drugs table with current database"""
        self.drugs_table.setRowCount(0)
        
        for drug in self.drug_database.drugs:
            row = self.drugs_table.rowCount()
            self.drugs_table.insertRow(row)
            
            profit = drug.base_price - drug.ingredient_cost
            
            self.drugs_table.setItem(row, 0, QTableWidgetItem(drug.name))
            self.drugs_table.setItem(row, 1, QTableWidgetItem(f"${drug.base_price:.2f}"))
            self.drugs_table.setItem(row, 2, QTableWidgetItem(f"${drug.ingredient_cost:.2f}"))
            self.drugs_table.setItem(row, 3, QTableWidgetItem(f"${profit:.2f}"))
            self.drugs_table.setItem(row, 4, QTableWidgetItem(f"{drug.profit_margin:.1f}%"))
    
    def update_ingredients_table(self):
        """Update the ingredients table with current database"""
        self.ingredients_table.setRowCount(0)
        
        for ingredient in self.ingredient_database.ingredients:
            row = self.ingredients_table.rowCount()
            self.ingredients_table.insertRow(row)
            
            self.ingredients_table.setItem(row, 0, QTableWidgetItem(ingredient.name))
            self.ingredients_table.setItem(row, 1, QTableWidgetItem(f"${ingredient.unit_price:.2f}"))
    
    def update_effects_table(self):
        """Update the effects table with current database"""
        self.effects_table.setRowCount(0)
        
        for effect in self.effect_database.effects:
            row = self.effects_table.rowCount()
            self.effects_table.insertRow(row)
            
            # Create item for effect name with color applied to text
            name_item = QTableWidgetItem(effect.name)
            name_item.setForeground(QColor(effect.color))
            
            self.effects_table.setItem(row, 0, name_item)
            self.effects_table.setItem(row, 1, QTableWidgetItem(effect.description))
    
    def new_database(self):
        """Create a new empty database"""
        if self.drug_database.drugs:
            confirm = QMessageBox.question(
                self, "Confirm New Database",
                "Are you sure you want to create a new database? Unsaved changes will be lost.",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.drug_database = DrugDatabase()
                # No need to reinitialize ingredient_database and effect_database as they're already initialized with hard-coded data
                self.current_file = None
                self.update_tables()
                self.statusBar().showMessage("Created new database")
        else:
            self.drug_database = DrugDatabase()
            # No need to reinitialize ingredient_database and effect_database as they're already initialized with hard-coded data
            self.current_file = None
            self.statusBar().showMessage("Created new database")
    
    def open_database(self):
        """Open a database file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Database", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Determine base path and filenames
                base_path = os.path.dirname(file_path)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # If the selected file ends with _drugs, strip that suffix to get the base name
                if base_name.endswith('_drugs'):
                    base_name = base_name[:-6]  # Remove '_drugs' suffix
                
                # Construct filename for drugs
                drugs_file = os.path.join(base_path, f"{base_name}_drugs.json")
                
                # Create new drug database (ingredients and effects are already initialized with hard-coded data)
                self.drug_database = DrugDatabase()
                
                # Load drugs data
                if os.path.exists(drugs_file):
                    self.drug_database.load_from_file(drugs_file)
                    self.current_file = base_name
                    self.statusBar().showMessage(f"Loaded drugs from {drugs_file}")
                
                # Update UI
                self.update_tables()
                self.statusBar().showMessage(f"Opened database: {base_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open database: {str(e)}")

    def save_database(self):
        """Save the database to the current file or prompt for a new file"""
        if self.current_file:
            try:
                # Construct filename for drugs only
                base_path = os.path.dirname(self.current_file) if os.path.dirname(self.current_file) else ""
                base_name = os.path.basename(self.current_file)
                
                drugs_file = os.path.join(base_path, f"{base_name}_drugs.json")
                
                # Save drugs data only (ingredients and effects are hard-coded)
                self.drug_database.save_to_file(drugs_file)
                
                self.statusBar().showMessage(f"Saved database: {base_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save database: {str(e)}")
        else:
            self.save_database_as()
    
    def save_database_as(self):
        """Save the database to a new file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Database As", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Get base name without extension
                base_path = os.path.dirname(file_path)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Remove _drugs suffix if present
                if base_name.endswith('_drugs'):
                    base_name = base_name[:-6]
                
                # Construct filename for drugs only
                drugs_file = os.path.join(base_path, f"{base_name}_drugs.json")
                
                # Save drugs data only (ingredients and effects are hard-coded)
                self.drug_database.save_to_file(drugs_file)
                
                self.current_file = base_name
                self.statusBar().showMessage(f"Saved database as: {base_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save database: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
