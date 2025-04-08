"""
Username dialog for the Schedule 1 Drug Recipe Calculator
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFormLayout)
from firebase_utils import firebase_manager


class SetUsernameDialog(QDialog):
    """Dialog for setting or updating a username"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Username")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Set a username that will be displayed when you submit drugs to the online database.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Current username (if any)
        current_username = firebase_manager.get_current_username()
        if current_username:
            current_label = QLabel(f"Current username: {current_username}")
            layout.addWidget(current_label)
        
        # Username input
        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username...")
        if current_username:
            self.username_input.setText(current_username)
        form_layout.addRow("Username:", self.username_input)
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.save_username)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_username(self):
        """Save the username to Firebase"""
        username = self.username_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, "Error", "Username cannot be empty")
            return
        
        # Check if username is valid (alphanumeric and underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            QMessageBox.warning(self, "Error", "Username can only contain letters, numbers, and underscores")
            return
        
        # Set the username
        result = firebase_manager.set_username(username)
        
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
            self.accept()
        else:
            QMessageBox.warning(self, "Error", result["message"])
