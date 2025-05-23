#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
                             QColorDialog, QSlider, QStyledItemDelegate, QTextBrowser, QCheckBox,
                             QInputDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel
from PyQt5.QtGui import QFont, QIcon, QColor

from models import Drug, Ingredient, DrugDatabase, IngredientDatabase, Effect, EffectDatabase
from firebase_utils import firebase_manager
from auth_dialogs import SignInDialog, SignUpDialog
from online_db_dialogs import SubmitDrugDialog, ViewOnlineDrugsDialog
from username_dialog import SetUsernameDialog
from announcement_tab import AnnouncementTab
from import_save_dialog import ImportSaveDialog


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
        
        # Drug type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["OG Kush", "Sour Diesel", "Green Crack", "Grandaddy Purple", "Meth", "Cocaine"])
        if drug:
            self.type_combo.setCurrentText(drug.drug_type)
        form_layout.addRow("Drug Type:", self.type_combo)
        
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
        name = self.name_input.text()
        base_price = self.price_input.value()
        notes = self.notes_input.toPlainText()
        drug_type = self.type_combo.currentText()
        
        return Drug(
            name=name,
            base_price=base_price,
            ingredients=self.ingredients.copy(),
            effects=self.effects.copy(),
            notes=notes,
            drug_type=drug_type
        )


# Remove unused proxy model


class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule 1 Drug Recipe Calculator")
        self.setMinimumSize(1000, 600)
        
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
        
        # Search and filter controls
        search_filter_layout = QHBoxLayout()
        
        # Search bar
        search_label = QLabel("Search:")
        self.drug_search_input = QLineEdit()
        self.drug_search_input.setPlaceholderText("Search by name, type, or effects...")
        self.drug_search_input.textChanged.connect(self.filter_drugs_table)
        search_filter_layout.addWidget(search_label)
        search_filter_layout.addWidget(self.drug_search_input)
        
        # Favorites filter
        self.show_favorites_checkbox = QCheckBox("Show Favorites Only")
        self.show_favorites_checkbox.stateChanged.connect(self.filter_drugs_table)
        search_filter_layout.addWidget(self.show_favorites_checkbox)
        
        drugs_layout.addLayout(search_filter_layout)
        
        # Drugs table
        self.drugs_table = QTableWidget(0, 7)  # Added column for favorite
        self.drugs_table.setHorizontalHeaderLabels(["Favorite", "Name", "Type", "Base Price", "Ingredient Cost", "Profit", "Profit Margin"])
        self.drugs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Name column stretches
        self.drugs_table.setColumnWidth(0, 70)  # Favorite column width
        
        # Enable sorting
        self.drugs_table.setSortingEnabled(True)
            
        drugs_layout.addWidget(self.drugs_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Drug")
        self.edit_button = QPushButton("Edit Drug")
        self.delete_button = QPushButton("Delete Drug")
        self.view_button = QPushButton("View Details")
        self.copy_button = QPushButton("Copy Drug")
        self.import_save_button = QPushButton("Import drugs from save")
        
        self.add_button.clicked.connect(self.add_drug)
        self.edit_button.clicked.connect(self.edit_drug)
        self.delete_button.clicked.connect(self.delete_drug)
        self.view_button.clicked.connect(self.view_drug_details)
        self.copy_button.clicked.connect(self.copy_drug)
        self.import_save_button.clicked.connect(self.import_from_save)
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.view_button)
        buttons_layout.addWidget(self.import_save_button)
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
        # Make name column smaller and description column stretch
        self.effects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.effects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.effects_table.setColumnWidth(0, 150)  # Set name column width to 150 pixels
        effects_layout.addWidget(self.effects_table)
        
        # Effect buttons
        effect_buttons_layout = QHBoxLayout()
        self.add_effect_button = QPushButton("Add Effect")
        self.edit_effect_button = QPushButton("Edit Effect")
        self.delete_effect_button = QPushButton("Delete Effect")
        self.view_effect_button = QPushButton("View Description")
        
        self.add_effect_button.clicked.connect(self.add_effect_to_db)
        self.edit_effect_button.clicked.connect(self.edit_effect_in_db)
        self.delete_effect_button.clicked.connect(self.delete_effect_from_db)
        self.view_effect_button.clicked.connect(self.view_effect_description)
        
        effect_buttons_layout.addWidget(self.add_effect_button)
        effect_buttons_layout.addWidget(self.edit_effect_button)
        effect_buttons_layout.addWidget(self.delete_effect_button)
        effect_buttons_layout.addWidget(self.view_effect_button)
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
        
        # Online Database tab
        online_db_tab = QWidget()
        online_db_layout = QVBoxLayout(online_db_tab)
        
        # Authentication status
        auth_layout = QHBoxLayout()
        self.auth_status_label = QLabel("Not signed in")
        self.sign_in_button = QPushButton("Sign In")
        self.sign_up_button = QPushButton("Sign Up")
        self.username_button = QPushButton("Set Username")
        
        self.sign_in_button.clicked.connect(self.handle_sign_in)
        self.sign_up_button.clicked.connect(self.handle_sign_up)
        self.username_button.clicked.connect(self.handle_set_username)
        self.username_button.setEnabled(False)  # Disabled until signed in
        
        auth_layout.addWidget(self.auth_status_label)
        auth_layout.addStretch()
        auth_layout.addWidget(self.sign_in_button)
        auth_layout.addWidget(self.sign_up_button)
        auth_layout.addWidget(self.username_button)
        online_db_layout.addLayout(auth_layout)
        
        # Search bar for online database
        online_search_layout = QHBoxLayout()
        online_search_label = QLabel("Search:")
        self.online_search_input = QLineEdit()
        self.online_search_input.setPlaceholderText("Search by name, type, or creator...")
        self.online_search_input.textChanged.connect(self.filter_online_drugs_table)
        online_search_layout.addWidget(online_search_label)
        online_search_layout.addWidget(self.online_search_input)
        online_db_layout.addLayout(online_search_layout)
        
        # Online drugs table
        self.online_drugs_table = QTableWidget(0, 6)
        self.online_drugs_table.setHorizontalHeaderLabels(["Name", "Type", "Base Price", "Submitted By", "Date", "Rating"])
        self.online_drugs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        # Enable sorting
        self.online_drugs_table.setSortingEnabled(True)
            
        online_db_layout.addWidget(self.online_drugs_table)
        
        # Online database buttons
        online_buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.view_online_button = QPushButton("View Details")
        self.import_button = QPushButton("Import Drug")
        self.my_submissions_button = QPushButton("My Submissions")
        
        self.refresh_button.clicked.connect(self.refresh_online_drugs)
        self.view_online_button.clicked.connect(self.view_online_drug_details)
        self.import_button.clicked.connect(self.import_online_drug)
        self.my_submissions_button.clicked.connect(self.view_my_submissions)
        
        online_buttons_layout.addWidget(self.refresh_button)
        online_buttons_layout.addWidget(self.view_online_button)
        online_buttons_layout.addWidget(self.import_button)
        online_buttons_layout.addWidget(self.my_submissions_button)
        online_db_layout.addLayout(online_buttons_layout)
        
        # Add file buttons to online tab too
        online_db_layout.addLayout(file_buttons_layout)
        
        # Create Announcements tab
        announcements_tab = AnnouncementTab(firebase_manager)
        
        # Add tabs
        self.tabs.addTab(drugs_tab, "Drugs")
        self.tabs.addTab(ingredients_tab, "Ingredients")
        self.tabs.addTab(effects_tab, "Effects")
        self.tabs.addTab(online_db_tab, "Online Database")
        self.tabs.addTab(announcements_tab, "Announcements")
        
        # Connect tab change event to load online drugs when switching to the Online Database tab
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initialize UI
        self.update_tables()
        self.update_auth_status()
        
        # Connect table cell click events
        self.drugs_table.cellClicked.connect(self.toggle_favorite)
    
    def on_tab_changed(self, index):
        """Handle tab change event"""
        # If switching to the Online Database tab (index 3), load the online drugs
        if index == 3:  # Online Database tab
            self.refresh_online_drugs()
        # If switching to the Announcements tab (index 4), refresh announcements
        elif index == 4:  # Announcements tab
            # Get the announcements tab widget and call its load_announcements method
            announcements_tab = self.tabs.widget(4)
            if hasattr(announcements_tab, 'load_announcements'):
                announcements_tab.load_announcements()
    
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
            # Get the drug name from the selected row (column 1 after adding favorites column)
            drug_name = self.drugs_table.item(selected_row, 1).text()
            
            # Find the drug in the database by name
            drug_index = -1
            for i, d in enumerate(self.drug_database.drugs):
                if d.name == drug_name:
                    drug_index = i
                    drug = d
                    break
                    
            if drug_index == -1:
                QMessageBox.warning(self, "Error", "Could not find the selected drug.")
                return
                
            dialog = AddDrugDialog(self, drug, self.ingredient_database, self.effect_database)
            if dialog.exec_():
                self.drug_database.drugs[drug_index] = dialog.get_drug()
                self.update_tables()
                self.statusBar().showMessage(f"Updated drug: {drug.name}")

    def copy_drug(self):
        """Create a copy of the selected drug"""
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug name from the selected row (column 1 after adding favorites column)
            drug_name = self.drugs_table.item(selected_row, 1).text()
            
            # Find the drug in the database by name
            drug = None
            for d in self.drug_database.drugs:
                if d.name == drug_name:
                    drug = d
                    break
                    
            if not drug:
                QMessageBox.warning(self, "Error", "Could not find the selected drug.")
                return
                
            # Create a copy with a new name
            new_name, ok = QInputDialog.getText(
                self, "Copy Drug", "Enter name for the copy:",
                QLineEdit.Normal, f"{drug.name} (Copy)"
            )
            
            if ok and new_name:
                # Check if the name already exists
                for d in self.drug_database.drugs:
                    if d.name == new_name:
                        QMessageBox.warning(self, "Error", f"A drug named '{new_name}' already exists.")
                        return
                
                # Create a deep copy of the drug
                new_drug = Drug(
                    name=new_name,
                    base_price=drug.base_price,
                    ingredients=[Ingredient(name=i.name, quantity=i.quantity, unit_price=i.unit_price) for i in drug.ingredients],
                    effects=[Effect(name=e.name, description=e.description, color=e.color) for e in drug.effects],
                    notes=drug.notes,
                    drug_type=drug.drug_type,
                    favorite=False  # Don't copy favorite status
                )
                
                # Add to database
                self.drug_database.add_drug(new_drug)
                self.update_tables()
                self.statusBar().showMessage(f"Created copy: {new_drug.name}")
    
    def import_from_save(self):
        """Import drug recipes from a Schedule I game save"""
        # Open the import save dialog
        from import_save_dialog import ImportSaveDialog
        dialog = ImportSaveDialog(self)
        
        if dialog.exec_():
            save_path, save_name = dialog.get_selected_save()
            if not save_path or not os.path.exists(save_path):
                QMessageBox.warning(self, "Error", "Invalid save path selected.")
                return
                
            # Look for drug recipes in the save file
            try:
                # First check for Products.json which contains the custom drug recipes
                products_json_path = os.path.join(save_path, "Products.json")
                if not os.path.exists(products_json_path):
                    QMessageBox.warning(self, "Error", "Products.json not found in the selected save.")
                    return
                    
                with open(products_json_path, 'r') as f:
                    products_data = json.load(f)
                
                # Check if there are any discovered products
                discovered_products = products_data.get("DiscoveredProducts", [])
                if not discovered_products:
                    QMessageBox.warning(self, "No Drugs Found", 
                                    f"No discovered drugs found in the save file for {save_name}.")
                    return
                
                # Get the mix recipes to trace ingredient chains
                mix_recipes = products_data.get("MixRecipes", [])
                
                # Get favorited products
                favorited_products = products_data.get("FavouritedProducts", [])
                
                # Get product prices
                product_prices = {}
                for price_data in products_data.get("ProductPrices", []):
                    product_id = price_data.get("String", "")
                    price = price_data.get("Int", 0)
                    if product_id and price:
                        product_prices[product_id] = price
                
                # Get created drug data (for effects and names)
                created_drugs = {}
                
                # Combine all created drug types
                for drug in products_data.get("CreatedWeed", []):
                    drug_id = drug.get("ID", "")
                    if drug_id:
                        created_drugs[drug_id] = drug
                
                for drug in products_data.get("CreatedMeth", []):
                    drug_id = drug.get("ID", "")
                    if drug_id:
                        created_drugs[drug_id] = drug
                        
                for drug in products_data.get("CreatedCocaine", []):
                    drug_id = drug.get("ID", "")
                    if drug_id:
                        created_drugs[drug_id] = drug
                
                # Create a dialog to let the user select which drug to import
                select_dialog = QDialog(self)
                select_dialog.setWindowTitle("Select Drugs to Import")
                select_dialog.setMinimumWidth(400)
                select_dialog.setMinimumHeight(500)
                
                layout = QVBoxLayout(select_dialog)
                layout.addWidget(QLabel(f"Select drugs to import from {save_name}:"))
                
                # Create a list widget with checkboxes for each drug
                drug_list = QListWidget()
                drug_list.setSelectionMode(QListWidget.MultiSelection)
                
                # Add discovered products to the list
                for product_id in discovered_products:
                    # Skip base ingredients that aren't actual drugs
                    if product_id in ["cuke", "banana", "paracetamol", "donut", "viagra", "mouthwash", 
                                     "flumedicine", "gasoline", "energydrink", "motoroil", "megabean", 
                                     "chili", "battery", "iodine", "addy", "horsesemen"]:
                        continue
                        
                    # Get the proper name from created drugs if available
                    display_name = product_id.capitalize()
                    if product_id in created_drugs:
                        display_name = created_drugs[product_id].get("Name", display_name)
                    
                    # Get the price if available
                    price = product_prices.get(product_id, 0)
                    
                    # Create the list item
                    item = QListWidgetItem(f"{display_name} (${price})")
                    item.setData(Qt.UserRole, product_id)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Checked)  # Default to checked
                    drug_list.addItem(item)
                
                layout.addWidget(drug_list)
                
                # Add buttons
                button_layout = QHBoxLayout()
                select_all_button = QPushButton("Select All")
                deselect_all_button = QPushButton("Deselect All")
                import_button = QPushButton("Import Selected")
                cancel_button = QPushButton("Cancel")
                
                select_all_button.clicked.connect(lambda: self.select_all_items(drug_list, True))
                deselect_all_button.clicked.connect(lambda: self.select_all_items(drug_list, False))
                import_button.clicked.connect(select_dialog.accept)
                cancel_button.clicked.connect(select_dialog.reject)
                
                button_layout.addWidget(select_all_button)
                button_layout.addWidget(deselect_all_button)
                button_layout.addWidget(import_button)
                button_layout.addWidget(cancel_button)
                
                layout.addLayout(button_layout)
                
                # Show the dialog
                if select_dialog.exec_():
                    # Get the selected drugs
                    selected_drugs = []
                    for i in range(drug_list.count()):
                        item = drug_list.item(i)
                        if item.checkState() == Qt.Checked:
                            selected_drugs.append(item.data(Qt.UserRole))
                    
                    if not selected_drugs:
                        QMessageBox.warning(self, "No Drugs Selected", "No drugs were selected for import.")
                        return
                    
                    # Import the selected drugs
                    drugs_imported = 0
                    for product_id in selected_drugs:
                        # Get drug details
                        drug_name = product_id.capitalize()
                        drug_type = "OG Kush"  # Default type
                        effects = []
                        
                        # Default drug category based on product_id
                        drug_category = "Weed"  # Default for most drugs
                        if product_id == "meth":
                            drug_category = "Meth"
                        elif product_id == "cocaine":
                            drug_category = "Cocaine"
                        
                        # Get proper name and effects if available in created drugs
                        if product_id in created_drugs:
                            drug_data = created_drugs[product_id]
                            drug_name = drug_data.get("Name", drug_name)
                            
                            # Determine drug category from numeric type
                            drug_type_num = drug_data.get("DrugType", 0)
                            if drug_type_num == 1:
                                drug_category = "Meth"
                            elif drug_type_num == 2:
                                drug_category = "Cocaine"
                            
                            # Get effects
                            for effect_id in drug_data.get("Properties", []):
                                # Map effect ID to proper effect name in our database
                                effect_name = self.map_effect_id_to_name(effect_id)
                                
                                # Try to find this effect in our database
                                effect = self.effect_database.get_effect(effect_name)
                                if effect:
                                    effects.append(effect)
                                else:
                                    # If not found, create a new effect with default values
                                    effects.append(Effect(name=effect_name))
                        
                        # Get price
                        base_price = float(product_prices.get(product_id, 0))
                        
                        # Check if this is a base drug (no recipe needed)
                        base_drugs = ["ogkush", "sourdiesel", "greencrack", "granddaddypurple", "cocaine", "meth"]
                        
                        if product_id in base_drugs:
                            # For base drugs, use empty ingredients list and map directly to drug type
                            ingredients = []
                            
                            # Map base drug ID to proper drug type
                            if product_id == "ogkush":
                                mix_drug_type = "OG Kush"
                                # Add base effect for OG Kush
                                calming_effect = self.effect_database.get_effect("Calming")
                                if calming_effect:
                                    effects.append(calming_effect)
                                else:
                                    effects.append(Effect(name="Calming"))
                            elif product_id == "sourdiesel":
                                mix_drug_type = "Sour Diesel"
                                # Add base effect for Sour Diesel
                                refreshing_effect = self.effect_database.get_effect("Refreshing")
                                if refreshing_effect:
                                    effects.append(refreshing_effect)
                                else:
                                    effects.append(Effect(name="Refreshing"))
                            elif product_id == "greencrack":
                                mix_drug_type = "Green Crack"
                                # Add base effect for Green Crack
                                energizing_effect = self.effect_database.get_effect("Energizing")
                                if energizing_effect:
                                    effects.append(energizing_effect)
                                else:
                                    effects.append(Effect(name="Energizing"))
                            elif product_id == "granddaddypurple":
                                mix_drug_type = "Grandaddy Purple"
                                # Add base effect for Grandaddy Purple
                                sedating_effect = self.effect_database.get_effect("Sedating")
                                if sedating_effect:
                                    effects.append(sedating_effect)
                                else:
                                    effects.append(Effect(name="Sedating"))
                            elif product_id == "cocaine":
                                mix_drug_type = "Cocaine"
                                # Cocaine has no base effects
                            elif product_id == "meth":
                                mix_drug_type = "Meth"
                                # Meth has no base effects
                            else:
                                mix_drug_type = product_id.capitalize()
                        else:
                            # For mixed drugs, trace the recipe chain
                            ingredients, mix_drug_type = self.trace_recipe_chain(product_id, mix_recipes, discovered_products)
                        
                        # Use the drug category (Weed, Meth, Cocaine) to determine the final drug type
                        final_drug_type = mix_drug_type
                        if drug_category == "Meth":
                            final_drug_type = "Meth"
                        elif drug_category == "Cocaine":
                            final_drug_type = "Cocaine"
                        
                        # Check if this product is favorited
                        is_favorited = product_id in favorited_products
                        
                        # Create the drug object
                        drug = Drug(
                            name=drug_name,
                            base_price=base_price,
                            ingredients=ingredients,
                            effects=effects,
                            drug_type=final_drug_type,
                            favorite=is_favorited
                        )
                        
                        # Add to our database
                        self.drug_database.add_drug(drug)
                        drugs_imported += 1
                    
                    # Update the UI
                    self.update_tables()
                    
                    if drugs_imported > 0:
                        QMessageBox.information(self, "Import Successful", 
                                            f"Successfully imported {drugs_imported} drug recipes from {save_name}.")
                    else:
                        QMessageBox.warning(self, "No Drugs Imported", 
                                            f"No valid drug recipes found in the save file for {save_name}.")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", 
                                    f"An error occurred while importing drugs from the save file:\n{str(e)}")
    
    def select_all_items(self, list_widget, checked):
        """Select or deselect all items in a list widget"""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            
    def map_effect_id_to_name(self, effect_id):
        """Map effect IDs from game save to our effect database names"""
        # Special case mappings
        effect_map = {
            "brighteyed": "Bright-Eyed",
            "caloriedense": "Calorie-Dense",
            "antigravity": "Anti-Gravity",
            "giraffying": "Long Faced",
            "seizure": "Seizure-Inducing",
            "thoughtprovoking": "Thought-Provoking",
            "tropicthunder": "Tropic Thunder",
            "glowie": "Glowing"  
        }
        
        # Check if this effect ID has a special mapping
        if effect_id.lower() in effect_map:
            return effect_map[effect_id.lower()]
        
        # Default: just capitalize the first letter
        return effect_id.capitalize()
        
    def map_base_drug_to_type(self, drug_id):
        """Map base drug IDs to their proper drug types"""
        if drug_id == "ogkush":
            return "OG Kush"
        elif drug_id == "sourdiesel":
            return "Sour Diesel"
        elif drug_id == "greencrack":
            return "Green Crack"
        elif drug_id == "granddaddypurple":
            return "Grandaddy Purple"
        elif drug_id == "cocaine":
            return "Cocaine"
        elif drug_id == "meth":
            return "Meth"
        else:
            # Default: just capitalize the first letter
            return drug_id.capitalize()
            
    def trace_recipe_chain(self, product_id, mix_recipes, discovered_products=None):
        """Trace the recipe chain to get all ingredients for a product
        Returns a tuple of (ingredients, drug_type)
        """
        # If discovered_products is not provided, use a default list
        if discovered_products is None:
            discovered_products = ["ogkush", "sourdiesel", "greencrack", "granddaddypurple", 
                                   "meth", "cocaine"]
        
        # Check if this is a base drug (no recipe needed)
        base_drugs = ["ogkush", "sourdiesel", "greencrack", "granddaddypurple", "cocaine", "meth"]
        if product_id in base_drugs:
            # For base drugs, return empty ingredients list and map directly to drug type
            drug_type = self.map_base_drug_to_type(product_id)
            return [], drug_type
        
        # Find the original weed strain used in the recipe chain
        original_strain = self.find_original_strain(product_id, mix_recipes)
        
        # If we couldn't find an original strain, use a default
        if not original_strain:
            original_strain = "ogkush"  # Default to OG Kush
        
        # Get all ingredients in the correct order (bottom to top)
        ingredient_ids = []
        self.trace_ingredients_backwards(product_id, mix_recipes, discovered_products, ingredient_ids, set())
        
        # Process the ingredients in the correct order from bottom to top in the JSON
        ingredients = []
        for ingredient_id in ingredient_ids:
            # Simply capitalize the first letter of the ingredient ID for the name
            ingredient_name = ingredient_id.capitalize()
            
            # Get the ingredient from our database if it exists
            ingredient = self.ingredient_database.get_ingredient(ingredient_name)
            if ingredient:
                # Create a copy with quantity 1
                ingredients.append(Ingredient(
                    name=ingredient.name,
                    quantity=1.0,
                    unit_price=ingredient.unit_price
                ))
            else:
                # If not found, create a default ingredient with the capitalized name
                ingredients.append(Ingredient(
                    name=ingredient_name,
                    quantity=1.0,
                    unit_price=5.0  # Default price
                ))
        
        # Map original strain to proper drug type
        drug_type = "OG Kush"  # Default type
        if original_strain:
            if original_strain == "ogkush":
                drug_type = "OG Kush"
            elif original_strain == "sourdiesel":
                drug_type = "Sour Diesel"
            elif original_strain == "greencrack":
                drug_type = "Green Crack"
            elif original_strain == "granddaddypurple":
                drug_type = "Grandaddy Purple"
            elif original_strain == "cocaine":
                drug_type = "Cocaine"
            elif original_strain == "meth":
                drug_type = "Meth"
        
        return ingredients, drug_type
        
    def build_recipe_tree(self, product_id, mix_recipes, drugs, recipe_tree, visited=None):
        """Build a complete recipe tree for a product
        This preserves the hierarchy of ingredients in the recipe chain
        """
        # Initialize visited set if not provided
        if visited is None:
            visited = set()
            
        # Create a copy of visited to avoid modifying the original
        # This allows the same ingredient to appear in different branches of the recipe tree
        local_visited = visited.copy()
        
        # Prevent infinite recursion
        if product_id in local_visited:
            return
            
        local_visited.add(product_id)
        
        # Find the recipe that produces this product
        for recipe in mix_recipes:
            if recipe.get("Output") == product_id:
                # Get the ingredients (product and mixer)
                product = recipe.get("Product")
                mixer = recipe.get("Mixer")
                
                # Initialize this node in the recipe tree
                # Use a unique ID for each node to handle duplicate ingredients
                node_id = f"{product_id}_{len(recipe_tree)}"
                recipe_tree[node_id] = {
                    "id": product_id,  # Store the actual product ID
                    "ingredients": []
                }
                
                # Process the product ingredient
                if product:
                    # If it's a drug (intermediate product), recursively build its recipe tree
                    if product in drugs:
                        self.build_recipe_tree(product, mix_recipes, drugs, recipe_tree, local_visited)
                        # Find the last node created for this product
                        for key in reversed(list(recipe_tree.keys())):
                            if recipe_tree[key].get("id") == product:
                                recipe_tree[node_id]["product"] = key
                                break
                    # If it's a base ingredient, add it directly
                    else:
                        recipe_tree[node_id]["ingredients"].append(product)
                
                # Process the mixer ingredient
                if mixer:
                    # If it's a drug (intermediate product), recursively build its recipe tree
                    if mixer in drugs:
                        self.build_recipe_tree(mixer, mix_recipes, drugs, recipe_tree, local_visited)
                        # Find the last node created for this mixer
                        for key in reversed(list(recipe_tree.keys())):
                            if recipe_tree[key].get("id") == mixer:
                                recipe_tree[node_id]["mixer"] = key
                                break
                    # If it's a base ingredient, add it directly
                    else:
                        recipe_tree[node_id]["ingredients"].append(mixer)
                
                break
    
    def flatten_recipe_tree(self, recipe_tree):
        """Flatten the recipe tree into a list of ingredients in the correct order
        This ensures ingredients are ordered from bottom to top in the recipe chain
        """
        # Start with an empty list
        ingredient_list = []
        
        # Process the recipe tree recursively
        self._flatten_node(recipe_tree, ingredient_list, set())
        
        return ingredient_list
    
    def _flatten_node(self, recipe_tree, ingredient_list, visited, node_id=None):
        """Helper function to recursively flatten the recipe tree
        """
        # If no node_id is provided, find the root node (the last one added)
        if node_id is None:
            # Get the keys in reverse order (newest first)
            keys = list(recipe_tree.keys())
            if keys:
                # Start with the last node added (the root of the tree)
                self._flatten_node(recipe_tree, ingredient_list, visited, keys[-1])
            return
        
        # Prevent processing the same node twice
        if node_id in visited:
            return
            
        visited.add(node_id)
        
        # Get the node data
        node = recipe_tree.get(node_id, {})
        
        # First process any product ingredient (which should come first in bottom-to-top order)
        if "product" in node:
            self._flatten_node(recipe_tree, ingredient_list, visited, node["product"])
        
        # Then process any mixer ingredient
        if "mixer" in node:
            self._flatten_node(recipe_tree, ingredient_list, visited, node["mixer"])
        
        # Finally add any direct ingredients from this node
        # Always add ingredients, even if they're duplicates
        for ingredient in node.get("ingredients", []):
            ingredient_list.append(ingredient)
    
    def trace_ingredients_backwards(self, product_id, mix_recipes, drugs, ingredient_ids, visited):
        """Trace the recipe chain backwards to get ingredients in the correct order
        This method works by starting from the final product and working backwards through the recipe chain
        """
        # Create a copy of visited to avoid modifying the original
        # This allows the same ingredient to appear in different branches of the recipe chain
        local_visited = visited.copy()
        
        # Prevent infinite recursion
        if product_id in local_visited:
            return
            
        local_visited.add(product_id)
        
        # Find the recipe that produces this product
        for recipe in mix_recipes:
            if recipe.get("Output") == product_id:
                # Get the ingredients (product and mixer)
                product = recipe.get("Product")
                mixer = recipe.get("Mixer")
                
                # Create a temporary list to hold ingredients from this level
                # This ensures we can insert them in the correct order
                temp_ingredients = []
                
                # Process the product ingredient first (this should come first in the final list)
                if product:
                    # If it's a drug, recursively trace its recipe
                    if product in drugs:
                        self.trace_ingredients_backwards(product, mix_recipes, drugs, ingredient_ids, local_visited)
                    # If it's a base ingredient, add it to our temporary list
                    else:
                        temp_ingredients.append(product)
                
                # Then process the mixer ingredient
                if mixer:
                    # If it's a drug, recursively trace its recipe
                    if mixer in drugs:
                        self.trace_ingredients_backwards(mixer, mix_recipes, drugs, ingredient_ids, local_visited)
                    # If it's a base ingredient, add it to our temporary list
                    else:
                        temp_ingredients.append(mixer)
                
                # Now add the temporary ingredients to the main list in reverse order
                # This ensures the mixer ingredient comes before the product ingredient
                # which matches the order in the game's recipe system
                for ingredient in reversed(temp_ingredients):
                    ingredient_ids.append(ingredient)
                
                break
    
    def find_original_strain(self, product_id, mix_recipes, visited=None):
        """Find the original weed strain used in a recipe chain
        This recursively traces back through the mix recipes to find the original strain
        """
        if visited is None:
            visited = set()
            
        # Prevent infinite recursion
        if product_id in visited:
            return None
            
        visited.add(product_id)
        
        # Base case: if this is one of the original strains, return it
        if product_id in ["ogkush", "sourdiesel", "greencrack", "granddaddypurple", "cocaine", "meth"]:
            return product_id
            
        # Find the recipe that produces this product
        for recipe in mix_recipes:
            if recipe.get("Output") == product_id:
                # Check the mixer first (usually the drug)
                mixer = recipe.get("Mixer")
                if mixer:
                    # If the mixer is an original strain, return it
                    if mixer in ["ogkush", "sourdiesel", "greencrack", "granddaddypurple", "cocaine", "meth"]:
                        return mixer
                    # Otherwise, recursively check the mixer
                    strain = self.find_original_strain(mixer, mix_recipes, visited)
                    if strain:
                        return strain
                        
                # Check the product ingredient
                product = recipe.get("Product")
                if product:
                    # If the product is an original strain, return it
                    if product in ["ogkush", "sourdiesel", "greencrack", "granddaddypurple", "cocaine", "meth"]:
                        return product
                    # Otherwise, recursively check the product
                    strain = self.find_original_strain(product, mix_recipes, visited)
                    if strain:
                        return strain
                        
        # If we couldn't find an original strain, return None
        return None

    
    def delete_drug(self):
        """Delete the selected drug"""
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug name from the selected row (column 1 after adding favorites column)
            drug_name = self.drugs_table.item(selected_row, 1).text()
            
            # Find the drug in the database by name
            drug_index = -1
            for i, d in enumerate(self.drug_database.drugs):
                if d.name == drug_name:
                    drug_index = i
                    drug = d
                    break
                    
            if drug_index == -1:
                QMessageBox.warning(self, "Error", "Could not find the selected drug.")
                return
                
            confirm = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete {drug.name}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.drug_database.drugs.pop(drug_index)
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
                
    def view_effect_description(self):
        """View the full description of the selected effect"""
        selected_row = self.effects_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Effect Selected", "Please select an effect to view its description.")
            return
        
        # Get the effect name and full description
        effect_name = self.effects_table.item(selected_row, 0).text()
        effect_description = self.effects_table.item(selected_row, 0).data(Qt.UserRole)
        
        # If no description is available, show a message
        if not effect_description:
            effect_description = "No description available for this effect."
        
        # Create and show a dialog with the description
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Effect Description: {effect_name}")
        dialog.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Add a label with the effect name in its color
        name_label = QLabel(effect_name)
        name_label.setFont(QFont("Arial", 14, QFont.Bold))
        effect = self.effect_database.get_effect(effect_name)
        if effect:
            name_label.setStyleSheet(f"color: {effect.color};")
        layout.addWidget(name_label)
        
        # Add a text browser for the description (allows for scrolling if needed)
        description_browser = QTextBrowser()
        description_browser.setPlainText(effect_description)
        description_browser.setFont(QFont("Arial", 12))
        layout.addWidget(description_browser)
        
        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec_()
    
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
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug name from the selected row (column 1 after adding favorites column)
            drug_name = self.drugs_table.item(selected_row, 1).text()
            
            # Find the drug in the database by name
            drug = None
            for d in self.drug_database.drugs:
                if d.name == drug_name:
                    drug = d
                    break
                    
            if not drug:
                QMessageBox.warning(self, "Error", "Could not find the selected drug.")
                return
            
            # Create a message box with drug details
            msg = QMessageBox(self)
            msg.setWindowTitle(f"Drug Details: {drug.name}")
            
            # Create a detailed message with drug information
            details = f"<h2>{drug.name}</h2>"
            details += f"<p><b>Drug Type:</b> {drug.drug_type}</p>"
            details += f"<p><b>Base Price:</b> ${drug.base_price:.2f}</p>"
            
            # Calculate recommended price (base price + 60% profit)
            recommended_price = drug.base_price * 1.6
            details += f"<p><b>Recommended Price:</b> ${recommended_price:.2f}</p>"
            
            # Calculate ingredient cost
            ingredient_cost = sum(ing.quantity * ing.unit_price for ing in drug.ingredients)
            details += f"<p><b>Ingredient Cost:</b> ${ingredient_cost:.2f}</p>"
            
            # Calculate profit
            profit = drug.base_price - ingredient_cost
            details += f"<p><b>Profit:</b> ${profit:.2f}</p>"
            
            # Calculate profit margin
            if ingredient_cost > 0:
                profit_margin = (profit / ingredient_cost) * 100
                details += f"<p><b>Profit Margin:</b> {profit_margin:.1f}%</p>"
            
            # Ingredients with numbered list instead of bullet points
            details += "<h3>Ingredients:</h3>"
            details += "<ol>"
            for ingredient in drug.ingredients:
                details += f"<li>{ingredient.name}: {ingredient.quantity} units at ${ingredient.unit_price:.2f} each = ${ingredient.quantity * ingredient.unit_price:.2f}</li>"
            details += "</ol>"
            
            # Effects
            details += "<h3>Effects:</h3>"
            details += "<ul>"
            for effect in drug.effects:
                color_style = f"background-color: {effect.color}; display: inline-block; width: 15px; height: 15px; margin-right: 5px;"
                details += f"<li><div style='{color_style}'></div> {effect.name}"
                if effect.description:
                    details += f": {effect.description}"
                details += "</li>"
            details += "</ul>"
            
            msg.setText(details)
            msg.setTextFormat(Qt.RichText)
            
            # Add buttons
            submit_button = msg.addButton("Submit to Online Database", QMessageBox.ActionRole)
            ok_button = msg.addButton(QMessageBox.Ok)
            
            msg.exec_()
            
            # Check which button was clicked
            if msg.clickedButton() == submit_button:
                self.submit_drug_to_online_db(drug)
    
    def update_auth_status(self):
        """Update the authentication status label"""
        if firebase_manager.is_authenticated():
            email = firebase_manager.get_current_user_email()
            username = firebase_manager.get_current_username()
            status_text = f"Signed in as: {email}"
            if username:
                status_text += f" (Username: {username})"
            self.auth_status_label.setText(status_text)
            self.sign_in_button.setText("Sign Out")
            self.sign_up_button.setVisible(False)
            self.username_button.setEnabled(True)
            self.my_submissions_button.setEnabled(True)
        else:
            self.auth_status_label.setText("Not signed in")
            self.sign_in_button.setText("Sign In")
            self.sign_up_button.setVisible(True)
            self.username_button.setEnabled(False)
            self.my_submissions_button.setEnabled(False)
    
    def handle_sign_in(self):
        """Handle sign in/out button click"""
        if firebase_manager.is_authenticated():
            # Sign out
            result = firebase_manager.sign_out()
            if result["success"]:
                QMessageBox.information(self, "Success", result["message"])
            else:
                QMessageBox.warning(self, "Error", result["message"])
        else:
            # Open sign in dialog
            dialog = SignInDialog(self)
            dialog.exec_()
        
        # Update UI
        self.update_auth_status()
        self.refresh_online_drugs()
    
    def handle_sign_up(self):
        """Handle sign up button click"""
        dialog = SignUpDialog(self)
        if dialog.exec_():
            QMessageBox.information(self, "Success", "Account created and signed in successfully")
            self.update_auth_status()
            self.refresh_online_drugs()
            
    def handle_set_username(self):
        """Open dialog to set or update username"""
        dialog = SetUsernameDialog(self)
        if dialog.exec_():
            self.update_auth_status()
            self.refresh_online_drugs()  # Refresh to show updated usernames
            
    def on_drug_table_header_clicked(self, logical_index):
        """Handle clicking on drug table header for sorting"""
        # Let the built-in sorting handle it
        pass
        
    def on_online_drug_table_header_clicked(self, logical_index):
        """Handle clicking on online drug table header for sorting"""
        # Let the built-in sorting handle it
        pass
    
    def filter_online_drugs_table(self):
        """Filter the online drugs table based on search text"""
        search_text = self.online_search_input.text().lower()
        
        for row in range(self.online_drugs_table.rowCount()):
            # Get drug name, type and creator for searching
            drug_name = self.online_drugs_table.item(row, 0).text().lower()
            drug_type = self.online_drugs_table.item(row, 1).text().lower()
            creator = self.online_drugs_table.item(row, 3).text().lower()
            
            # Get the full drug data for searching in effects
            drug_data = self.online_drugs_table.item(row, 0).data(Qt.UserRole)
            
            # Check if row should be visible based on search
            if search_text and search_text not in drug_name and search_text not in drug_type and search_text not in creator:
                # Try to search in effects if available
                effect_match = False
                if drug_data and "effects" in drug_data:
                    for effect in drug_data["effects"]:
                        effect_name = effect.get("name", "").lower()
                        if search_text in effect_name:
                            effect_match = True
                            break
                
                if not effect_match:
                    self.online_drugs_table.setRowHidden(row, True)
                else:
                    self.online_drugs_table.setRowHidden(row, False)
            else:
                self.online_drugs_table.setRowHidden(row, False)
    
    def submit_drug_to_online_db(self, drug):
        """Submit a drug to the online database"""
        dialog = SubmitDrugDialog(self, drug)
        if dialog.exec_():
            self.statusBar().showMessage(f"Drug {drug.name} submitted to online database")
            self.refresh_online_drugs()
    
    def refresh_online_drugs(self):
        """Refresh the online drugs table"""
        # Temporarily disable sorting to prevent issues while updating
        sorting_enabled = self.online_drugs_table.isSortingEnabled()
        self.online_drugs_table.setSortingEnabled(False)
        
        # Store the current sort column and order
        sort_column = self.online_drugs_table.horizontalHeader().sortIndicatorSection()
        sort_order = self.online_drugs_table.horizontalHeader().sortIndicatorOrder()
        
        # Clear the table
        self.online_drugs_table.setRowCount(0)
        
        # Get drugs from Firebase
        drugs = firebase_manager.get_all_drugs()
        
        # Populate the table
        for i, drug_data in enumerate(drugs):
            self.online_drugs_table.insertRow(i)
            
            # Name
            name_item = QTableWidgetItem(drug_data.get("name", ""))
            name_item.setData(Qt.UserRole, drug_data)  # Store the full drug data
            
            # Drug type
            drug_type = drug_data.get("drug_type", "OG Kush")  # Default to Weed if not specified
            type_item = QTableWidgetItem(drug_type)
            
            # Base price
            base_price = drug_data.get("base_price", 0)
            base_price_item = QTableWidgetItem(f"${base_price:.2f}")
            base_price_item.setData(Qt.UserRole, base_price)
            
            # Submitted by
            username = drug_data.get("username", None)
            user_email = drug_data.get("user_email", "Unknown")
            display_name = username if username else user_email
            submitted_by_item = QTableWidgetItem(display_name)
            
            # Date
            timestamp = drug_data.get("timestamp", None)
            date_str = "Unknown"
            sort_timestamp = 0
            if timestamp:
                # Handle Firestore DatetimeWithNanoseconds object
                try:
                    # If it's already a datetime object (from Firestore)
                    date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                    sort_timestamp = timestamp.timestamp()  # Convert to Unix timestamp for sorting
                except AttributeError:
                    # If it's a Unix timestamp (milliseconds)
                    from datetime import datetime
                    date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")
                    sort_timestamp = timestamp / 1000  # Convert to seconds for sorting
            
            date_item = QTableWidgetItem()
            date_item.setData(Qt.DisplayRole, date_str)
            date_item.setData(Qt.UserRole, sort_timestamp)  # For sorting
            
            # Rating (upvotes)
            upvotes = drug_data.get("upvotes", 0)
            rating_item = QTableWidgetItem(f"{upvotes} 👍")
            rating_item.setData(Qt.UserRole, upvotes)
            
            # Set items in the table
            self.online_drugs_table.setItem(i, 0, name_item)
            self.online_drugs_table.setItem(i, 1, type_item)
            self.online_drugs_table.setItem(i, 2, base_price_item)
            self.online_drugs_table.setItem(i, 3, submitted_by_item)
            self.online_drugs_table.setItem(i, 4, date_item)
            self.online_drugs_table.setItem(i, 5, rating_item)
        
        # Re-enable sorting if it was enabled before
        self.online_drugs_table.setSortingEnabled(sorting_enabled)
        
        # Re-apply the sort if it was active
        if sorting_enabled and sort_column >= 0:
            self.online_drugs_table.sortItems(sort_column, sort_order)
        
        self.statusBar().showMessage(f"Loaded {len(drugs)} drugs from online database")
    
    def view_online_drug_details(self):
        """View details of the selected online drug"""
        selected_row = self.online_drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug data from the UserRole data of the name column
            drug_data = self.online_drugs_table.item(selected_row, 0).data(Qt.UserRole)
            if not drug_data:
                QMessageBox.warning(self, "Error", "Could not find the selected drug data.")
                return
                
            # Create a dialog to show the details
            from online_db_dialogs import DrugDetailsDialog
            dialog = DrugDetailsDialog(self, drug_data)
            dialog.exec_()
    
    def import_online_drug(self):
        """Import the selected drug from the online database"""
        selected_row = self.online_drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug data from the UserRole data of the name column
            drug_data = self.online_drugs_table.item(selected_row, 0).data(Qt.UserRole)
            if not drug_data:
                QMessageBox.warning(self, "Error", "Could not find the selected drug data.")
                return
            if drug_data:
                # Convert to Drug object
                drug = Drug.from_firebase_dict(drug_data)
                
                # Add to local database
                self.drug_database.add_drug(drug)
                self.update_tables()
                self.statusBar().showMessage(f"Imported drug: {drug.name}")
    
    def view_my_submissions(self):
        """View drugs submitted by the current user"""
        if not firebase_manager.is_authenticated():
            QMessageBox.warning(self, "Error", "You must be signed in to view your submissions")
            return
        
        # Open a dialog showing all online drugs
        dialog = ViewOnlineDrugsDialog(self, my_submissions=True)
        result = dialog.exec_()
        
        # Only update if a drug was selected for import and dialog was accepted
        if result and hasattr(dialog, "drug_to_import") and dialog.drug_to_import is not None:
            # Import the drug if one was selected
            self.drug_database.add_drug(dialog.drug_to_import)
            self.update_tables()
            self.statusBar().showMessage(f"Imported drug: {dialog.drug_to_import.name}")
    
    def update_tables(self):
        """Update both the drugs and ingredients tables"""
        self.update_drugs_table()
        self.update_ingredients_table()
        self.update_effects_table()
    
    def filter_drugs_table(self):
        """Filter the drugs table based on search text and favorites"""
        search_text = self.drug_search_input.text().lower()
        show_favorites_only = self.show_favorites_checkbox.isChecked()
        
        for row in range(self.drugs_table.rowCount()):
            # Get drug name and type for searching
            drug_name = self.drugs_table.item(row, 1).text().lower()
            drug_type = self.drugs_table.item(row, 2).text().lower()
            
            # Get favorite status
            is_favorite = self.drugs_table.item(row, 0).data(Qt.UserRole)
            
            # Check if row should be visible based on search and favorites filter
            if show_favorites_only and not is_favorite:
                self.drugs_table.setRowHidden(row, True)
            elif search_text and search_text not in drug_name and search_text not in drug_type:
                # Try to search in effects if available
                effect_match = False
                drug_index = -1
                for i, drug in enumerate(self.drug_database.drugs):
                    if drug.name == self.drugs_table.item(row, 1).text():
                        drug_index = i
                        break
                        
                if drug_index >= 0:
                    for effect in self.drug_database.drugs[drug_index].effects:
                        if search_text in effect.name.lower():
                            effect_match = True
                            break
                            
                if not effect_match:
                    self.drugs_table.setRowHidden(row, True)
                else:
                    self.drugs_table.setRowHidden(row, False)
            else:
                self.drugs_table.setRowHidden(row, False)
    
    def toggle_favorite(self, row, column):
        """Toggle favorite status when clicking on the favorite column"""
        if column == 0:  # Favorite column
            # Get the drug from the database
            drug_name = self.drugs_table.item(row, 1).text()
            for i, drug in enumerate(self.drug_database.drugs):
                if drug.name == drug_name:
                    # Toggle favorite status
                    drug.favorite = not drug.favorite
                    self.drug_database.drugs[i] = drug
                    
                    # Update the table cell
                    favorite_item = self.drugs_table.item(row, 0)
                    favorite_item.setText("★" if drug.favorite else "☆")
                    favorite_item.setData(Qt.UserRole, drug.favorite)
                    
                    # Apply color to indicate favorite status
                    if drug.favorite:
                        favorite_item.setForeground(QColor("gold"))
                    else:
                        favorite_item.setForeground(QColor("gray"))
                    break
    
    def update_drugs_table(self):
        """Update the drugs table with current database"""
        # Temporarily disable sorting to prevent issues while updating
        sorting_enabled = self.drugs_table.isSortingEnabled()
        self.drugs_table.setSortingEnabled(False)
        self.drugs_table.setRowCount(0)
        
        # Store the current sort column and order
        sort_column = self.drugs_table.horizontalHeader().sortIndicatorSection()
        sort_order = self.drugs_table.horizontalHeader().sortIndicatorOrder()
        
        # Get search text and favorites filter
        search_text = self.drug_search_input.text().lower() if hasattr(self, 'drug_search_input') else ""
        show_favorites_only = self.show_favorites_checkbox.isChecked() if hasattr(self, 'show_favorites_checkbox') else False
        
        for drug in self.drug_database.drugs:
            # Apply filters
            if show_favorites_only and not drug.favorite:
                continue
                
            if search_text and search_text not in drug.name.lower() and search_text not in drug.drug_type.lower():
                # Also search in effects
                effect_match = False
                for effect in drug.effects:
                    if search_text in effect.name.lower():
                        effect_match = True
                        break
                if not effect_match:
                    continue
            
            row = self.drugs_table.rowCount()
            self.drugs_table.insertRow(row)
            
            profit = drug.base_price - drug.ingredient_cost
            
            # Create favorite item
            favorite_item = QTableWidgetItem("★" if drug.favorite else "☆")
            favorite_item.setData(Qt.UserRole, drug.favorite)
            if drug.favorite:
                favorite_item.setForeground(QColor("gold"))
            else:
                favorite_item.setForeground(QColor("gray"))
            
            # Create items with appropriate sort values
            name_item = QTableWidgetItem(drug.name)
            
            # Drug type
            type_item = QTableWidgetItem(drug.drug_type)
            
            # Base price
            base_price_item = QTableWidgetItem(f"${drug.base_price:.2f}")
            base_price_item.setData(Qt.UserRole, drug.base_price)
            
            # Ingredient cost
            ingredient_cost_item = QTableWidgetItem(f"${drug.ingredient_cost:.2f}")
            ingredient_cost_item.setData(Qt.UserRole, drug.ingredient_cost)
            
            # Profit
            profit_item = QTableWidgetItem(f"${profit:.2f}")
            profit_item.setData(Qt.UserRole, profit)
            
            # Profit margin
            profit_margin_item = QTableWidgetItem(f"{drug.profit_margin:.1f}%")
            profit_margin_item.setData(Qt.UserRole, drug.profit_margin)
            
            self.drugs_table.setItem(row, 0, favorite_item)
            self.drugs_table.setItem(row, 1, name_item)
            self.drugs_table.setItem(row, 2, type_item)
            self.drugs_table.setItem(row, 3, base_price_item)
            self.drugs_table.setItem(row, 4, ingredient_cost_item)
            self.drugs_table.setItem(row, 5, profit_item)
            self.drugs_table.setItem(row, 6, profit_margin_item)
        
        # Re-enable sorting if it was enabled before
        self.drugs_table.setSortingEnabled(sorting_enabled)
        
        # Re-apply the sort if it was active
        if sorting_enabled and sort_column >= 0:
            self.drugs_table.sortItems(sort_column, sort_order)
    
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
            
            # Create a truncated description (first 50 characters + "..." if longer)
            desc = effect.description
            if len(desc) > 50:
                desc = desc[:50] + "..."
            
            self.effects_table.setItem(row, 0, name_item)
            self.effects_table.setItem(row, 1, QTableWidgetItem(desc))
            
            # Store the full description as user data for later retrieval
            self.effects_table.item(row, 0).setData(Qt.UserRole, effect.description)
    
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
