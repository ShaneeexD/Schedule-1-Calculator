"""
Online Database dialogs for the Schedule 1 Drug Recipe Calculator
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFormLayout,
                           QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from firebase_utils import firebase_manager
from models import Drug
from username_dialog import SetUsernameDialog


class SubmitDrugDialog(QDialog):
    """Dialog for submitting a drug to the online database"""
    def __init__(self, parent=None, drug=None):
        super().__init__(parent)
        self.setWindowTitle("Submit Drug to Online Database")
        self.setMinimumWidth(500)
        
        # Store the drug
        self.drug = drug
        
        # Create layout
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Submit this drug to the online database for other users to see and use.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Drug info
        if drug:
            drug_info = QLabel(f"Drug: {drug.name}\nType: {drug.drug_type}\nBase Price: ${drug.base_price:.2f}\nIngredient Cost: ${drug.ingredient_cost:.2f}\nProfit Margin: {drug.profit_margin:.1f}%")
            layout.addWidget(drug_info)
            
            # Ingredients summary
            ingredients_label = QLabel(f"Ingredients: {len(drug.ingredients)}")
            layout.addWidget(ingredients_label)
            
            # Effects summary
            effects_label = QLabel(f"Effects: {len(drug.effects)}")
            layout.addWidget(effects_label)
        
        # Additional comments
        form_layout = QFormLayout()
        self.comments_input = QTextEdit()
        self.comments_input.setPlaceholderText("Add any additional comments about this drug...")
        form_layout.addRow("Comments:", self.comments_input)
        layout.addLayout(form_layout)
        
        # Authentication status
        self.auth_status_label = QLabel("Not signed in")
        layout.addWidget(self.auth_status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.sign_in_button = QPushButton("Sign In")
        self.submit_button = QPushButton("Submit Drug")
        self.cancel_button = QPushButton("Cancel")
        
        self.sign_in_button.clicked.connect(self.handle_sign_in)
        self.submit_button.clicked.connect(self.submit_drug)
        self.cancel_button.clicked.connect(self.reject)
        
        # Enable/disable submit button based on authentication
        self.submit_button.setEnabled(firebase_manager.is_authenticated())
        
        button_layout.addWidget(self.sign_in_button)
        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Update authentication status after all UI elements are created
        self.update_auth_status()
    
    def update_auth_status(self):
        """Update the authentication status label"""
        if firebase_manager.is_authenticated():
            self.auth_status_label.setText(f"Signed in as: {firebase_manager.get_current_user_email()}")
            self.sign_in_button.setText("Sign Out")
            self.submit_button.setEnabled(True)
        else:
            self.auth_status_label.setText("Not signed in")
            self.sign_in_button.setText("Sign In")
            self.submit_button.setEnabled(False)
    
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
            from auth_dialogs import SignInDialog
            dialog = SignInDialog(self)
            dialog.exec_()
        
        # Update UI
        self.update_auth_status()
    
    def submit_drug(self):
        """Submit the drug to the online database"""
        if not firebase_manager.is_authenticated():
            QMessageBox.warning(self, "Error", "You must be signed in to submit a drug")
            return
        
        if not self.drug:
            QMessageBox.warning(self, "Error", "No drug to submit")
            return
        
        # Prepare drug data for Firebase
        drug_data = self.drug.to_firebase_dict()
        
        # Add comments
        drug_data["comments"] = self.comments_input.toPlainText()
        
        # Submit to Firebase
        result = firebase_manager.submit_drug(drug_data)
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
            self.accept()
        else:
            QMessageBox.warning(self, "Error", result["message"])


class ViewOnlineDrugsDialog(QDialog):
    """Dialog for viewing online drugs"""
    def __init__(self, parent=None, my_submissions=False):
        super().__init__(parent)
        self.setWindowTitle("Online Drugs" if not my_submissions else "My Submissions")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.my_submissions = my_submissions
        self.drug_to_import = None
        
        # Create layout
        layout = QVBoxLayout()
        
        # Authentication status
        self.auth_status_label = QLabel("Not signed in")
        layout.addWidget(self.auth_status_label)
        
        # Initialize UI elements before updating auth status
        # Auth buttons
        auth_layout = QHBoxLayout()
        self.sign_in_button = QPushButton("Sign In")
        self.sign_in_button.clicked.connect(self.handle_sign_in)
        self.username_button = QPushButton("Set Username")
        self.username_button.clicked.connect(self.handle_set_username)
        self.username_button.setEnabled(False)  # Disabled until signed in
        
        auth_layout.addWidget(self.sign_in_button)
        auth_layout.addWidget(self.username_button)
        auth_layout.addStretch()
        layout.addLayout(auth_layout)
        
        # Drugs table
        self.drugs_table = QTableWidget(0, 8)
        self.drugs_table.setHorizontalHeaderLabels(["Name", "Type", "Base Price", "Ingredient Cost", "Profit Margin", "Submitted By", "Date", "Upvotes"])
        self.drugs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.drugs_table.setSortingEnabled(True)  # Enable sorting
        self.drugs_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        layout.addWidget(self.drugs_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.view_button = QPushButton("View Details")
        self.import_button = QPushButton("Import Drug")
        self.delete_button = QPushButton("Delete")
        self.help_button = QPushButton("How do I submit a drug?")
        self.close_button = QPushButton("Close")
        
        self.refresh_button.clicked.connect(self.refresh_drugs)
        self.view_button.clicked.connect(self.view_drug_details)
        self.import_button.clicked.connect(self.import_drug)
        self.delete_button.clicked.connect(self.delete_drug)
        self.help_button.clicked.connect(self.show_submission_help)
        self.close_button.clicked.connect(self.accept)
        
        # Only show delete button if authenticated
        self.delete_button.setVisible(firebase_manager.is_authenticated())
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.view_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.help_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Now update auth status after all UI elements are created
        self.update_auth_status()
        
        # Load drugs
        self.refresh_drugs()
    
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
            self.username_button.setEnabled(True)
            self.delete_button.setVisible(True)
        else:
            self.auth_status_label.setText("Not signed in")
            self.sign_in_button.setText("Sign In")
            self.username_button.setEnabled(False)
            self.delete_button.setVisible(False)
    
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
            from auth_dialogs import SignInDialog
            dialog = SignInDialog(self)
            dialog.exec_()
        
        # Update UI
        self.update_auth_status()
        self.refresh_drugs()
        
    def handle_set_username(self):
        """Open dialog to set or update username"""
        dialog = SetUsernameDialog(self)
        if dialog.exec_():
            self.update_auth_status()
            self.refresh_drugs()  # Refresh to show updated usernames
            
    def on_header_clicked(self, logical_index):
        """Handle clicking on table header for sorting"""
        # Let the built-in sorting handle it
        pass
        
    def show_submission_help(self):
        """Show a dialog explaining how to submit a drug to the online database"""
        msg = QMessageBox(self)
        msg.setWindowTitle("How to Submit a Drug")
        msg.setIcon(QMessageBox.Information)
        
        help_text = (
            "<h3>How to submit a drug to the online database:</h3>"
            "<ol>"
            "<li>Go to the <b>Drugs</b> tab in the main application</li>"
            "<li>Select the drug you want to submit</li>"
            "<li>Click the <b>View Details</b> button</li>"
            "<li>In the details dialog, click the <b>Submit to Online Database</b> button</li>"
            "<li>Add any comments about your drug (optional)</li>"
            "<li>Click <b>Submit Drug</b></li>"
            "</ol>"
            "<p>Note: You must be signed in to submit drugs to the online database.</p>"
        )
        
        msg.setText(help_text)
        msg.setTextFormat(Qt.RichText)
        msg.exec_()
    
    def refresh_drugs(self):
        """Refresh the drugs table"""
        # Temporarily disable sorting to prevent issues while updating
        sorting_enabled = self.drugs_table.isSortingEnabled()
        self.drugs_table.setSortingEnabled(False)
        
        # Store the current sort column and order
        sort_column = self.drugs_table.horizontalHeader().sortIndicatorSection()
        sort_order = self.drugs_table.horizontalHeader().sortIndicatorOrder()
        
        # Clear the table
        self.drugs_table.setRowCount(0)
        
        # Get drugs from Firebase
        if self.my_submissions:
            drugs = firebase_manager.get_user_drugs()
        else:
            drugs = firebase_manager.get_all_drugs()
        
        # Populate the table
        for i, drug_data in enumerate(drugs):
            self.drugs_table.insertRow(i)
            
            # Name
            name_item = QTableWidgetItem(drug_data.get("name", ""))
            name_item.setData(Qt.UserRole, drug_data)  # Store the full drug data
            
            # Drug type
            drug_type = drug_data.get("drug_type", "Weed")  # Default to Weed if not specified
            type_item = QTableWidgetItem(drug_type)
            
            # Base price
            base_price = drug_data.get("base_price", 0)
            base_price_item = QTableWidgetItem(f"${base_price:.2f}")
            base_price_item.setData(Qt.UserRole, base_price)
            
            # Ingredient cost
            ingredient_cost = drug_data.get("ingredient_cost", 0)
            ingredient_cost_item = QTableWidgetItem(f"${ingredient_cost:.2f}")
            ingredient_cost_item.setData(Qt.UserRole, ingredient_cost)
            
            # Profit margin
            profit_margin = drug_data.get("profit_margin", 0)
            profit_margin_item = QTableWidgetItem(f"{profit_margin:.1f}%")
            profit_margin_item.setData(Qt.UserRole, profit_margin)
            
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
            
            # Upvotes
            upvotes = drug_data.get("upvotes", 0)
            upvotes_item = QTableWidgetItem(f"{upvotes} 👍")
            upvotes_item.setData(Qt.UserRole, upvotes)
            
            # Set items in the table
            self.drugs_table.setItem(i, 0, name_item)
            self.drugs_table.setItem(i, 1, type_item)
            self.drugs_table.setItem(i, 2, base_price_item)
            self.drugs_table.setItem(i, 3, ingredient_cost_item)
            self.drugs_table.setItem(i, 4, profit_margin_item)
            self.drugs_table.setItem(i, 5, submitted_by_item)
            self.drugs_table.setItem(i, 6, date_item)
            self.drugs_table.setItem(i, 7, upvotes_item)
    
    def view_drug_details(self):
        """View details of the selected drug"""
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug data from the UserRole data of the name column
            drug_data = self.drugs_table.item(selected_row, 0).data(Qt.UserRole)
            if not drug_data:
                QMessageBox.warning(self, "Error", "Could not find the selected drug data.")
                return
                
            # Create a dialog to show the details
            dialog = DrugDetailsDialog(self, drug_data)
            dialog.exec_()
    
    def import_drug(self):
        """Import the selected drug into the local database"""
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug data from the UserRole data of the name column
            drug_data = self.drugs_table.item(selected_row, 0).data(Qt.UserRole)
            if not drug_data:
                QMessageBox.warning(self, "Error", "Could not find the selected drug data.")
                return
                
            # Convert to Drug object
            drug = Drug.from_firebase_dict(drug_data)
            
            # Signal to parent that we want to import this drug
            self.drug_to_import = drug
            self.accept()
    
    def delete_drug(self):
        """Delete the selected drug from the online database"""
        if not firebase_manager.is_authenticated():
            QMessageBox.warning(self, "Error", "You must be signed in to delete a drug")
            return
        
        selected_row = self.drugs_table.currentRow()
        if selected_row >= 0:
            # Get the drug data from the UserRole data of the name column
            drug_data = self.drugs_table.item(selected_row, 0).data(Qt.UserRole)
            if not drug_data:
                QMessageBox.warning(self, "Error", "Could not find the selected drug data.")
                return
            
            # Confirm deletion
            drug_name = drug_data.get("name", "Unknown")
            confirm = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete {drug_name} from the online database?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Delete from Firebase
                result = firebase_manager.delete_drug(drug_data.get("id"))
                if result["success"]:
                    QMessageBox.information(self, "Success", result["message"])
                    self.refresh_drugs()
                else:
                    QMessageBox.warning(self, "Error", result["message"])


class DrugDetailsDialog(QDialog):
    """Dialog for viewing details of a drug from the online database"""
    def __init__(self, parent=None, drug_data=None):
        super().__init__(parent)
        self.setWindowTitle("Drug Details")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.drug_data = drug_data
        
        # Create layout
        layout = QVBoxLayout()
        
        if drug_data:
            # Basic info
            info_layout = QFormLayout()
            info_layout.addRow("Name:", QLabel(drug_data.get("name", "")))
            info_layout.addRow("Drug Type:", QLabel(drug_data.get("drug_type", "Weed")))
            info_layout.addRow("Base Price:", QLabel(f"${drug_data.get('base_price', 0):.2f}"))
            info_layout.addRow("Ingredient Cost:", QLabel(f"${drug_data.get('ingredient_cost', 0):.2f}"))
            info_layout.addRow("Profit Margin:", QLabel(f"{drug_data.get('profit_margin', 0):.1f}%"))
            
            # Upvotes
            upvotes = drug_data.get("upvotes", 0)
            upvotes_layout = QHBoxLayout()
            upvotes_label = QLabel(f"Upvotes: {upvotes}")
            self.upvote_button = QPushButton("👍 Upvote")
            self.upvote_button.clicked.connect(self.upvote_drug)
            
            # Check if user has already upvoted this drug
            drug_id = drug_data.get("id")
            if firebase_manager.has_upvoted_drug(drug_id):
                self.upvote_button.setText("✓ Upvoted")
                self.upvote_button.setEnabled(False)
            elif not firebase_manager.is_authenticated():
                self.upvote_button.setEnabled(False)
                self.upvote_button.setToolTip("Sign in to upvote")
                
            upvotes_layout.addWidget(upvotes_label)
            upvotes_layout.addWidget(self.upvote_button)
            upvotes_layout.addStretch()
            info_layout.addRow("", upvotes_layout)
            
            # Submitted by
            username = drug_data.get("username", None)
            user_email = drug_data.get("user_email", "Unknown")
            display_name = username if username else user_email
            info_layout.addRow("Submitted By:", QLabel(display_name))
            
            # Date
            timestamp = drug_data.get("timestamp", None)
            date_str = "Unknown"
            if timestamp:
                # Handle Firestore DatetimeWithNanoseconds object
                try:
                    # If it's already a datetime object (from Firestore)
                    date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                except AttributeError:
                    # If it's a Unix timestamp (milliseconds)
                    from datetime import datetime
                    date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")
            info_layout.addRow("Date:", QLabel(date_str))
            
            # Comments
            if "comments" in drug_data and drug_data["comments"]:
                comments_label = QLabel(drug_data["comments"])
                comments_label.setWordWrap(True)
                info_layout.addRow("Comments:", comments_label)
            
            layout.addLayout(info_layout)
            
            # Ingredients
            ingredients_label = QLabel("Ingredients:")
            ingredients_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(ingredients_label)
            
            ingredients_table = QTableWidget(0, 4)
            ingredients_table.setHorizontalHeaderLabels(["Name", "Quantity", "Unit Price", "Total Cost"])
            ingredients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            layout.addWidget(ingredients_table)
            
            # Populate ingredients
            ingredients = drug_data.get("ingredients", [])
            for i, ing in enumerate(ingredients):
                ingredients_table.insertRow(i)
                ingredients_table.setItem(i, 0, QTableWidgetItem(ing.get("name", "")))
                ingredients_table.setItem(i, 1, QTableWidgetItem(str(ing.get("quantity", 0))))
                ingredients_table.setItem(i, 2, QTableWidgetItem(f"${ing.get('unit_price', 0):.2f}"))
                ingredients_table.setItem(i, 3, QTableWidgetItem(f"${ing.get('total_cost', 0):.2f}"))
            
            # Effects
            effects_label = QLabel("Effects:")
            effects_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(effects_label)
            
            effects_table = QTableWidget(0, 2)
            effects_table.setHorizontalHeaderLabels(["Name", "Description"])
            effects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            layout.addWidget(effects_table)
            
            # Populate effects
            effects = drug_data.get("effects", [])
            for i, effect in enumerate(effects):
                effects_table.insertRow(i)
                
                # Create item for effect name with color applied as background
                name_item = QTableWidgetItem(effect.get("name", ""))
                color = effect.get("color", "#FFFFFF")
                name_item.setBackground(QColor(color))
                # Set text color to black or white depending on background brightness
                color_obj = QColor(color)
                brightness = (color_obj.red() * 299 + color_obj.green() * 587 + color_obj.blue() * 114) / 1000
                if brightness > 128:
                    name_item.setForeground(QColor(0, 0, 0))  # Black text for light backgrounds
                else:
                    name_item.setForeground(QColor(255, 255, 255))  # White text for dark backgrounds
                
                effects_table.setItem(i, 0, name_item)
                effects_table.setItem(i, 1, QTableWidgetItem(effect.get("description", "")))
        
        # Close button
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def upvote_drug(self):
        """Upvote the drug"""
        if not self.drug_data:
            return
            
        drug_id = self.drug_data.get("id")
        if not drug_id:
            return
            
        result = firebase_manager.upvote_drug(drug_id)
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
            self.upvote_button.setText("✓ Upvoted")
            self.upvote_button.setEnabled(False)
            
            # Update the upvotes count in the drug data
            self.drug_data["upvotes"] = result["upvotes"]
            
            # Refresh the parent dialog if it exists
            parent = self.parent()
            if parent and hasattr(parent, "refresh_drugs"):
                parent.refresh_drugs()
        else:
            QMessageBox.warning(self, "Error", result["message"])
