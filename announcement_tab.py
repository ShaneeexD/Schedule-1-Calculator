#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QListWidgetItem, QTextBrowser, 
                            QPushButton, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QDate, QUrl
from PyQt5.QtGui import QFont, QColor, QDesktopServices
import re
from datetime import datetime

class AnnouncementTab(QWidget):
    """Widget for displaying announcements in the main application"""
    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase = firebase_manager
        self.announcements = []
        
        # Create layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Header
        header_label = QLabel("Announcements")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header_label)
        
        # Splitter for list and details
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - announcement list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        list_label = QLabel("Recent Announcements")
        list_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.announcement_list = QListWidget()
        self.announcement_list.currentItemChanged.connect(self.on_announcement_selected)
        
        left_layout.addWidget(list_label)
        left_layout.addWidget(self.announcement_list)
        
        # Right panel - announcement details
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setWordWrap(True)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: gray;")
        
        # Use QTextBrowser instead of QTextEdit to support clickable links
        self.content_display = QTextBrowser()
        self.content_display.setReadOnly(True)
        self.content_display.setOpenExternalLinks(True)  # Open links in external browser
        # Connect the anchorClicked signal to handle link clicks
        self.content_display.anchorClicked.connect(self.handle_link_clicked)
        
        right_layout.addWidget(self.title_label)
        right_layout.addWidget(self.date_label)
        right_layout.addWidget(self.content_display)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 400])  # Set initial sizes
        
        # Refresh button
        refresh_button = QPushButton("Refresh Announcements")
        refresh_button.clicked.connect(self.load_announcements)
        main_layout.addWidget(refresh_button)
        
        # Load announcements
        self.load_announcements()
    
    def load_announcements(self):
        """Load announcements from Firebase"""
        self.announcement_list.clear()
        self.title_label.clear()
        self.date_label.clear()
        self.content_display.clear()
        
        try:
            # Get announcements from Firebase
            announcements_ref = self.firebase.db.collection('announcements')
            announcements = announcements_ref.get()
            
            self.announcements = []
            for doc in announcements:
                announcement_data = doc.to_dict()
                announcement_data['id'] = doc.id
                
                # Check if announcement has expired
                if 'expiry_date' in announcement_data:
                    try:
                        expiry_date = announcement_data['expiry_date']
                        if expiry_date:
                            year, month, day = map(int, expiry_date.split('-'))
                            expiry_qdate = QDate(year, month, day)
                            current_date = QDate.currentDate()
                            
                            # Skip expired announcements
                            if expiry_qdate < current_date:
                                continue
                    except Exception as e:
                        print(f"Error parsing expiry date: {e}")
                
                self.announcements.append(announcement_data)
            
            # Sort announcements by date (newest first) and importance
            self.announcements.sort(key=lambda x: (not x.get('important', False), 
                                                 x.get('date_created', '')), 
                                   reverse=True)
            
            # Add to list widget
            for announcement in self.announcements:
                item = QListWidgetItem(announcement.get('title', 'Untitled'))
                
                # Mark important announcements in red
                if announcement.get('important', False):
                    item.setForeground(Qt.red)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                self.announcement_list.addItem(item)
                
            # Select first item if available
            if self.announcement_list.count() > 0:
                self.announcement_list.setCurrentRow(0)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load announcements: {str(e)}")
    
    def on_announcement_selected(self, current, previous):
        """Handle announcement selection"""
        if not current:
            return
        
        index = self.announcement_list.currentRow()
        if 0 <= index < len(self.announcements):
            announcement = self.announcements[index]
            
            self.title_label.setText(announcement.get('title', 'Untitled'))
            
            date_str = announcement.get('date_created', '')
            date_text = f"Posted: {date_str}"
            
            self.date_label.setText(date_text)
            

            
            # Process content to make links clickable
            content = announcement.get('content', '')
            content = self.process_links(content)
            self.content_display.setHtml(content)
            
            # Highlight important announcements
            if announcement.get('important', False):
                self.title_label.setStyleSheet("color: red;")
            else:
                self.title_label.setStyleSheet("")
    
    def process_links(self, text):
        """Process text to make URLs clickable"""
        # URL pattern - matches http, https, ftp URLs
        url_pattern = r'(https?://[\w\d:#@%/;$()~_?\+-=\\.&]*)'  
        
        # Replace URLs with HTML anchor tags
        html_text = re.sub(url_pattern, r'<a href="\1">\1</a>', text)
        
        # Convert newlines to HTML breaks
        html_text = html_text.replace('\n', '<br>')
        
        return html_text
    
    def handle_link_clicked(self, url):
        """Handle when a link is clicked in the announcement"""
        # Open the URL in the default web browser
        QDesktopServices.openUrl(url)
