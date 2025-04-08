"""
Firebase utilities for the Schedule 1 Drug Recipe Calculator
"""
import os
import json
import datetime
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# Import hardcoded credentials
from firebase_credentials import FIREBASE_CONFIG, SERVICE_ACCOUNT_INFO

# Firebase configuration
firebase_config = FIREBASE_CONFIG

# Initialize Firebase Authentication
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Initialize Firestore with hardcoded credentials
try:
    # Use the service account info from firebase_credentials.py
    service_account_info = SERVICE_ACCOUNT_INFO
    
    # Check if all required credentials are available
    if all(service_account_info.values()):
        cred = credentials.Certificate(service_account_info)
        try:
            firebase_admin.initialize_app(cred)
        except ValueError:
            # App already initialized
            pass
        db = firestore.client()
    else:
        print("Warning: Some Firebase service account credentials are missing in environment variables")
        print("Please check your .env file and ensure all FIREBASE_* variables are set")
        db = None
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    db = None

class FirebaseManager:
    """Manages Firebase authentication and database operations"""
    def __init__(self):
        self.user = None
        self.id_token = None
        self.refresh_token = None
        self.local_id = None
        self.email = None
        self.username = None
        
        # Path for storing auth tokens
        self.token_path = Path(os.path.dirname(__file__)) / 'auth_token.pickle'
        
        # Try to load saved tokens
        self.load_auth_tokens()
    
    def sign_up(self, email: str, password: str) -> Dict:
        """Create a new user account"""
        try:
            user = auth.create_user_with_email_and_password(email, password)
            self.user = user
            self.id_token = user['idToken']
            self.refresh_token = user['refreshToken']
            self.local_id = user['localId']
            self.email = email
            return {"success": True, "message": "Account created successfully"}
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message:
                return {"success": False, "message": "Email already exists"}
            elif "WEAK_PASSWORD" in error_message:
                return {"success": False, "message": "Password should be at least 6 characters"}
            else:
                return {"success": False, "message": f"Error: {error_message}"}
    
    def sign_in(self, email: str, password: str) -> Dict:
        """Sign in with email and password"""
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            self.user = user
            self.id_token = user['idToken']
            self.refresh_token = user['refreshToken']
            self.local_id = user['localId']
            self.email = email
            
            # Save tokens for persistent authentication
            self.save_auth_tokens()
            
            return {"success": True, "message": "Signed in successfully"}
        except Exception as e:
            error_message = str(e)
            if "INVALID_PASSWORD" in error_message:
                return {"success": False, "message": "Invalid password"}
            elif "EMAIL_NOT_FOUND" in error_message:
                return {"success": False, "message": "Email not found"}
            else:
                return {"success": False, "message": f"Error: {error_message}"}
    
    def sign_out(self) -> Dict:
        """Sign out the current user"""
        try:
            self.user = None
            self.id_token = None
            self.refresh_token = None
            self.local_id = None
            self.email = None
            
            # Remove saved tokens
            if self.token_path.exists():
                self.token_path.unlink()
                
            return {"success": True, "message": "Signed out successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        # If we have a token but it's expired, try to refresh it
        if self.refresh_token and not self.id_token:
            try:
                user = auth.refresh(self.refresh_token)
                self.id_token = user['idToken']
                self.user = user
                self.save_auth_tokens()
            except Exception:
                # If refresh fails, consider user not authenticated
                return False
                
        return self.id_token is not None
        
    def save_auth_tokens(self):
        """Save authentication tokens to file for persistence"""
        if self.refresh_token and self.email:
            token_data = {
                'refresh_token': self.refresh_token,
                'email': self.email,
                'local_id': self.local_id,
                'username': self.username
            }
            with open(self.token_path, 'wb') as f:
                pickle.dump(token_data, f)
    
    def load_auth_tokens(self):
        """Load authentication tokens from file"""
        if self.token_path.exists():
            try:
                with open(self.token_path, 'rb') as f:
                    token_data = pickle.load(f)
                    
                self.refresh_token = token_data.get('refresh_token')
                self.email = token_data.get('email')
                self.local_id = token_data.get('local_id')
                self.username = token_data.get('username')
                
                # If user is authenticated but doesn't have a username, try to load it
                if self.is_authenticated() and not self.username:
                    self.load_username()
                
                # We'll refresh the ID token when needed in is_authenticated()
            except Exception as e:
                print(f"Error loading auth tokens: {e}")
    
    def get_current_user_email(self) -> Optional[str]:
        """Get the email of the current user"""
        return self.email
    
    def get_current_user_id(self) -> Optional[str]:
        """Get the ID of the current user"""
        return self.local_id
        
    def get_current_username(self) -> Optional[str]:
        """Get the username of the current user"""
        if not self.username and self.is_authenticated():
            self.load_username()
        return self.username
        
    def set_username(self, username: str) -> Dict:
        """Set or update the username for the current user"""
        if not self.is_authenticated():
            return {"success": False, "message": "User not authenticated"}
            
        try:
            # Check if username already exists for another user
            users_ref = db.collection("users").where("username", "==", username).stream()
            for user in users_ref:
                user_data = user.to_dict()
                if user_data.get("user_id") != self.local_id:
                    return {"success": False, "message": "Username already taken"}
            
            # Update or create user document
            user_ref = db.collection("users").document(self.local_id)
            user_ref.set({
                "user_id": self.local_id,
                "email": self.email,
                "username": username
            }, merge=True)
            
            self.username = username
            self.save_auth_tokens()
            
            return {"success": True, "message": "Username set successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def load_username(self) -> None:
        """Load username from Firestore"""
        if not self.is_authenticated():
            return
            
        try:
            user_ref = db.collection("users").document(self.local_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                self.username = user_data.get("username")
                self.save_auth_tokens()
        except Exception as e:
            print(f"Error loading username: {str(e)}")
    
    def submit_drug(self, drug_data: Dict) -> Dict:
        """Submit a drug to the online database"""
        if not self.is_authenticated():
            return {"success": False, "message": "User not authenticated"}
        
        try:
            # Add user information to the drug data
            drug_data["user_id"] = self.local_id
            drug_data["user_email"] = self.email
            drug_data["timestamp"] = datetime.datetime.now()
            
            # Add username if available
            if self.username:
                drug_data["username"] = self.username
            
            # Initialize ratings
            drug_data["upvotes"] = 0
            drug_data["upvoted_by"] = []
            
            # Add the drug data to Firestore
            doc_ref = db.collection("drugs").document()
            doc_ref.set(drug_data)
            return {"success": True, "message": "Drug submitted successfully", "drug_id": doc_ref.id}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_all_drugs(self) -> List[Dict]:
        """Get all drugs from the online database"""
        try:
            drugs_ref = db.collection("drugs").stream()
            
            result = []
            for doc in drugs_ref:
                drug_data = doc.to_dict()
                drug_data["id"] = doc.id
                result.append(drug_data)
            
            return result
        except Exception as e:
            print(f"Error getting drugs: {str(e)}")
            return []
    
    def get_user_drugs(self) -> List[Dict]:
        """Get drugs submitted by the current user"""
        if not self.is_authenticated():
            return []
        
        try:
            drugs_ref = db.collection("drugs").where("user_id", "==", self.local_id).stream()
            
            result = []
            for doc in drugs_ref:
                drug_data = doc.to_dict()
                drug_data["id"] = doc.id
                result.append(drug_data)
            
            return result
        except Exception as e:
            print(f"Error getting user drugs: {str(e)}")
            return []
    
    def delete_drug(self, drug_id: str) -> Dict:
        """Delete a drug from the online database"""
        if not self.is_authenticated():
            return {"success": False, "message": "User not authenticated"}
        
        try:
            # First check if the drug belongs to the current user
            doc_ref = db.collection("drugs").document(drug_id)
            drug = doc_ref.get()
            
            if not drug.exists:
                return {"success": False, "message": "Drug not found"}
            
            drug_data = drug.to_dict()
            if drug_data["user_id"] != self.local_id:
                return {"success": False, "message": "You can only delete your own drugs"}
            
            # Delete the drug
            doc_ref.delete()
            return {"success": True, "message": "Drug deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def upvote_drug(self, drug_id: str) -> Dict:
        """Upvote a drug in the online database"""
        if not self.is_authenticated():
            return {"success": False, "message": "User not authenticated"}
        
        try:
            # Get the drug document
            doc_ref = db.collection("drugs").document(drug_id)
            drug = doc_ref.get()
            
            if not drug.exists:
                return {"success": False, "message": "Drug not found"}
            
            drug_data = drug.to_dict()
            
            # Check if user has already upvoted this drug
            upvoted_by = drug_data.get("upvoted_by", [])
            if self.local_id in upvoted_by:
                return {"success": False, "message": "You have already upvoted this drug"}
            
            # Update upvotes count and add user to upvoted_by list
            upvotes = drug_data.get("upvotes", 0) + 1
            upvoted_by.append(self.local_id)
            
            # Update the drug document
            doc_ref.update({
                "upvotes": upvotes,
                "upvoted_by": upvoted_by
            })
            
            return {"success": True, "message": "Drug upvoted successfully", "upvotes": upvotes}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def has_upvoted_drug(self, drug_id: str) -> bool:
        """Check if the current user has upvoted a drug"""
        if not self.is_authenticated():
            return False
        
        try:
            # Get the drug document
            doc_ref = db.collection("drugs").document(drug_id)
            drug = doc_ref.get()
            
            if not drug.exists:
                return False
            
            drug_data = drug.to_dict()
            upvoted_by = drug_data.get("upvoted_by", [])
            
            return self.local_id in upvoted_by
        except Exception as e:
            print(f"Error checking if user has upvoted drug: {str(e)}")
            return False
    
    def get_drug_by_id(self, drug_id: str) -> Optional[Dict]:
        """Get a drug by its ID"""
        try:
            doc_ref = db.collection("drugs").document(drug_id)
            drug = doc_ref.get()
            
            if not drug.exists:
                return None
            
            drug_data = drug.to_dict()
            drug_data["id"] = drug.id
            return drug_data
        except Exception as e:
            print(f"Error getting drug: {str(e)}")
            return None

# Create a global instance of FirebaseManager
firebase_manager = FirebaseManager()
