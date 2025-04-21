#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QListWidgetItem, QPushButton, 
                            QMessageBox, QFileDialog, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ImportSaveDialog(QDialog):
    """Dialog for importing data from Schedule I game saves"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from Schedule I Save")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Initialize variables
        self.selected_save_path = None
        self.selected_save_name = None
        
        # Create layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Header
        header_label = QLabel("Select a save file to import:")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(header_label)
        
        # Instructions
        instructions = QLabel("This will import drug recipes from your Schedule I game save.")
        main_layout.addWidget(instructions)
        
        # Save list
        self.save_list = QListWidget()
        self.save_list.setAlternatingRowColors(True)
        self.save_list.currentItemChanged.connect(self.on_save_selected)
        main_layout.addWidget(self.save_list)
        
        # Save details
        self.save_details = QLabel("Select a save to view details")
        self.save_details.setWordWrap(True)
        self.save_details.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        main_layout.addWidget(self.save_details)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.browse_button = QPushButton("Browse for Save Folder...")
        self.browse_button.clicked.connect(self.browse_for_save)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_saves)
        
        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.accept)
        self.import_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.browse_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Load saves
        self.load_saves()
    
    def load_saves(self):
        """Load available Schedule I saves"""
        self.save_list.clear()
        self.import_button.setEnabled(False)
        self.save_details.setText("Select a save to view details")
        
        # Default save location
        default_save_path = self.get_default_save_path()
        if not default_save_path or not os.path.exists(default_save_path):
            self.save_details.setText("No default save location found. Use 'Browse' to locate your saves folder.")
            return
        
        # Find all steam ID folders
        steam_ids = []
        try:
            for item in os.listdir(default_save_path):
                steam_id_path = os.path.join(default_save_path, item)
                if os.path.isdir(steam_id_path):
                    steam_ids.append(item)
        except Exception as e:
            self.save_details.setText(f"Error accessing save directory: {str(e)}")
            return
        
        if not steam_ids:
            self.save_details.setText("No Steam ID folders found in the save location.")
            return
        
        # Find all save games for each steam ID
        saves_found = False
        for steam_id in steam_ids:
            steam_id_path = os.path.join(default_save_path, steam_id)
            
            try:
                for save_folder in os.listdir(steam_id_path):
                    save_path = os.path.join(steam_id_path, save_folder)
                    
                    if os.path.isdir(save_path):
                        # Check for Game.json
                        game_json_path = os.path.join(save_path, "Game.json")
                        if os.path.exists(game_json_path):
                            # Read organization name from Game.json
                            try:
                                with open(game_json_path, 'r') as f:
                                    game_data = json.load(f)
                                    org_name = game_data.get("OrganisationName", "Unknown")
                                    game_version = game_data.get("GameVersion", "Unknown")
                                    
                                    # Create list item
                                    display_name = f"{org_name} ({save_folder}, {game_version})"
                                    item = QListWidgetItem(display_name)
                                    item.setData(Qt.UserRole, {
                                        "path": save_path,
                                        "name": org_name,
                                        "folder": save_folder,
                                        "version": game_version,
                                        "steam_id": steam_id
                                    })
                                    self.save_list.addItem(item)
                                    saves_found = True
                            except Exception as e:
                                print(f"Error reading Game.json from {game_json_path}: {str(e)}")
            except Exception as e:
                print(f"Error accessing Steam ID folder {steam_id_path}: {str(e)}")
        
        if not saves_found:
            self.save_details.setText("No valid save games found. Use 'Browse' to locate your saves folder.")
    
    def get_default_save_path(self) -> Optional[str]:
        """Get the default Schedule I save path"""
        # Default path is in AppData/LocalLow/TVGS/Schedule I/Saves/
        appdata_local_low = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'LocalLow')
        if os.path.exists(appdata_local_low):
            save_path = os.path.join(appdata_local_low, 'TVGS', 'Schedule I', 'Saves')
            if os.path.exists(save_path):
                return save_path
        return None
    
    def browse_for_save(self):
        """Browse for a save folder"""
        default_path = self.get_default_save_path() or os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'LocalLow')
        
        # Open folder dialog
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Schedule I Saves Folder", default_path
        )
        
        if folder_path:
            # Check if this is a valid save folder structure
            if self.is_valid_save_structure(folder_path):
                # Update the save list with this folder
                self.update_save_list_from_folder(folder_path)
            else:
                QMessageBox.warning(
                    self, "Invalid Folder", 
                    "The selected folder does not appear to be a valid Schedule I save location. "
                    "Please select the 'Saves' folder or a specific save folder."
                )
    
    def is_valid_save_structure(self, folder_path: str) -> bool:
        """Check if the folder has a valid save structure"""
        # Check if this is the Saves folder (contains Steam ID folders)
        for item in os.listdir(folder_path):
            steam_id_path = os.path.join(folder_path, item)
            if os.path.isdir(steam_id_path):
                # Check if this folder contains save folders
                for save_item in os.listdir(steam_id_path):
                    save_path = os.path.join(steam_id_path, save_item)
                    if os.path.isdir(save_path) and os.path.exists(os.path.join(save_path, "Game.json")):
                        return True
        
        # Check if this is a Steam ID folder (contains save folders)
        for item in os.listdir(folder_path):
            save_path = os.path.join(folder_path, item)
            if os.path.isdir(save_path) and os.path.exists(os.path.join(save_path, "Game.json")):
                return True
        
        # Check if this is a specific save folder (contains Game.json)
        if os.path.exists(os.path.join(folder_path, "Game.json")):
            return True
        
        return False
    
    def update_save_list_from_folder(self, folder_path: str):
        """Update the save list based on the selected folder"""
        self.save_list.clear()
        
        # Check if this is a specific save folder (contains Game.json)
        game_json_path = os.path.join(folder_path, "Game.json")
        if os.path.exists(game_json_path):
            try:
                with open(game_json_path, 'r') as f:
                    game_data = json.load(f)
                    org_name = game_data.get("OrganisationName", "Unknown")
                    game_version = game_data.get("GameVersion", "Unknown")
                    
                    # Create list item
                    save_folder = os.path.basename(folder_path)
                    steam_id = os.path.basename(os.path.dirname(folder_path))
                    
                    display_name = f"{org_name} ({save_folder}, {game_version})"
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.UserRole, {
                        "path": folder_path,
                        "name": org_name,
                        "folder": save_folder,
                        "version": game_version,
                        "steam_id": steam_id
                    })
                    self.save_list.addItem(item)
            except Exception as e:
                print(f"Error reading Game.json from {game_json_path}: {str(e)}")
            return
        
        # Check if this is a Steam ID folder (contains save folders)
        saves_found = False
        for item in os.listdir(folder_path):
            save_path = os.path.join(folder_path, item)
            if os.path.isdir(save_path):
                game_json_path = os.path.join(save_path, "Game.json")
                if os.path.exists(game_json_path):
                    try:
                        with open(game_json_path, 'r') as f:
                            game_data = json.load(f)
                            org_name = game_data.get("OrganisationName", "Unknown")
                            game_version = game_data.get("GameVersion", "Unknown")
                            
                            # Create list item
                            save_folder = os.path.basename(save_path)
                            steam_id = os.path.basename(folder_path)
                            
                            display_name = f"{org_name} ({save_folder}, {game_version})"
                            item = QListWidgetItem(display_name)
                            item.setData(Qt.UserRole, {
                                "path": save_path,
                                "name": org_name,
                                "folder": save_folder,
                                "version": game_version,
                                "steam_id": steam_id
                            })
                            self.save_list.addItem(item)
                            saves_found = True
                    except Exception as e:
                        print(f"Error reading Game.json from {game_json_path}: {str(e)}")
        
        if saves_found:
            return
        
        # Check if this is the Saves folder (contains Steam ID folders)
        for item in os.listdir(folder_path):
            steam_id_path = os.path.join(folder_path, item)
            if os.path.isdir(steam_id_path):
                for save_item in os.listdir(steam_id_path):
                    save_path = os.path.join(steam_id_path, save_item)
                    if os.path.isdir(save_path):
                        game_json_path = os.path.join(save_path, "Game.json")
                        if os.path.exists(game_json_path):
                            try:
                                with open(game_json_path, 'r') as f:
                                    game_data = json.load(f)
                                    org_name = game_data.get("OrganisationName", "Unknown")
                                    game_version = game_data.get("GameVersion", "Unknown")
                                    
                                    # Create list item
                                    display_name = f"{org_name} ({save_item}, {game_version})"
                                    item = QListWidgetItem(display_name)
                                    item.setData(Qt.UserRole, {
                                        "path": save_path,
                                        "name": org_name,
                                        "folder": save_item,
                                        "version": game_version,
                                        "steam_id": item
                                    })
                                    self.save_list.addItem(item)
                            except Exception as e:
                                print(f"Error reading Game.json from {game_json_path}: {str(e)}")
    
    def on_save_selected(self, current, previous):
        """Handle save selection"""
        if not current:
            self.import_button.setEnabled(False)
            self.save_details.setText("Select a save to view details")
            return
        
        # Get save data
        save_data = current.data(Qt.UserRole)
        if not save_data:
            return
        
        self.selected_save_path = save_data["path"]
        self.selected_save_name = save_data["name"]
        
        # Enable import button
        self.import_button.setEnabled(True)
        
        # Update details
        details = f"""
        <b>Organization:</b> {save_data['name']}
        <br><b>Save Folder:</b> {save_data['folder']}
        <br><b>Game Version:</b> {save_data['version']}
        <br><b>Steam ID:</b> {save_data['steam_id']}
        <br><b>Path:</b> {save_data['path']}
        """
        self.save_details.setText(details)
    
    def get_selected_save(self) -> Tuple[Optional[str], Optional[str]]:
        """Return the selected save path and name"""
        return self.selected_save_path, self.selected_save_name


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ImportSaveDialog()
    if dialog.exec_():
        save_path, save_name = dialog.get_selected_save()
        print(f"Selected save: {save_name} at {save_path}")
    sys.exit(0)
