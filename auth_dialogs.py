"""
Authentication dialogs for the Schedule 1 Drug Recipe Calculator
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt
from firebase_utils import firebase_manager


class SignInDialog(QDialog):
    """Dialog for signing in with email and password"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign In")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QFormLayout()
        
        # Email
        self.email_input = QLineEdit()
        layout.addRow("Email:", self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.sign_in_button = QPushButton("Sign In")
        self.sign_up_button = QPushButton("Sign Up")
        self.forgot_password_button = QPushButton("Forgot Password")
        self.cancel_button = QPushButton("Cancel")
        
        self.sign_in_button.clicked.connect(self.sign_in)
        self.sign_up_button.clicked.connect(self.open_sign_up)
        self.forgot_password_button.clicked.connect(self.open_password_reset)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.sign_in_button)
        button_layout.addWidget(self.sign_up_button)
        button_layout.addWidget(self.forgot_password_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
    
    def sign_in(self):
        """Sign in with email and password"""
        email = self.email_input.text()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter email and password")
            return
        
        result = firebase_manager.sign_in(email, password)
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
            self.accept()
        else:
            QMessageBox.warning(self, "Error", result["message"])
    
    def open_sign_up(self):
        """Open the sign up dialog"""
        self.reject()
        dialog = SignUpDialog(self.parent())
        if dialog.exec_():
            self.accept()
            
    def open_password_reset(self):
        """Send password reset email"""
        email = self.email_input.text()
        
        if not email:
            QMessageBox.warning(self, "Error", "Please enter your email address first")
            return
        
        result = firebase_manager.reset_password(email)
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
        else:
            QMessageBox.warning(self, "Error", result["message"])


class SignUpDialog(QDialog):
    """Dialog for signing up with email and password"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign Up")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QFormLayout()
        
        # Email
        self.email_input = QLineEdit()
        layout.addRow("Email:", self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_input)
        
        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Confirm Password:", self.confirm_password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.sign_up_button = QPushButton("Sign Up")
        self.cancel_button = QPushButton("Cancel")
        
        self.sign_up_button.clicked.connect(self.sign_up)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.sign_up_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
    
    def sign_up(self):
        """Sign up with email and password"""
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not email or not password or not confirm_password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        
        result = firebase_manager.sign_up(email, password)
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
            self.accept()
        else:
            QMessageBox.warning(self, "Error", result["message"])
