import sys
import openai
import os
import json
import re
import sqlite3
from datetime import datetime
from PyQt6.QtGui import (QFont, QColor, QDesktopServices, QIcon, QPixmap, QCursor, QMovie)
from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QCheckBox, QGraphicsDropShadowEffect, QStackedWidget,
                             QScrollArea, QFrame, QListWidget, QListWidgetItem, QCalendarWidget,
                             QTabWidget, QInputDialog, QComboBox, QSizePolicy, QTextEdit,
                             QDialog, QFileDialog, QMessageBox)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

openai.api_key = "your_api_key_here"


STYLESHEET = """
    QWidget {
        background-color: #f9fafb;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        color: #2e343b;
    }
    QPushButton {
        background-color: #3b82f6;
        color: white;
        padding: 10px 16px;
        border-radius: 10px;
        font-weight: 600;
        transition: background-color 0.25s ease;
        border: none;
    }
    QPushButton:hover {
        background-color: #2563eb;
    }
    QPushButton:pressed {
        background-color: #1d4ed8;
    }
    QPushButton:disabled {
        background-color: #9ca3af;
        color: #d1d5db;
    }
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
        border: 1.5px solid #d1d5db;
        border-radius: 8px;
        padding: 8px;
        background-color: white;
        font-size: 14px;
        selection-background-color: #60a5fa;
        selection-color: white;
    }
    QLineEdit:hover, QTextEdit:hover, QComboBox:hover {
        border-color: #3b82f6;
    }
    QListWidget {
        background-color: white;
        border: 1.5px solid #d1d5db;
        padding: 6px;
        border-radius: 8px;
    }
    QTabWidget::pane {
        border: 1.5px solid #cbd5e1;
        background: white;
        border-radius: 8px;
    }
    QTabBar::tab {
        background: #e0e7ff;
        padding: 10px 16px;
        border-radius: 8px 8px 0 0;
        margin-right: 4px;
        font-weight: 600;
        color: #374151;
    }
    QTabBar::tab:selected {
        background: #6366f1;
        color: white;
    }
    QLabel {
        font-size: 14px;
        color: #1f2937;
    }
    QCheckBox {
        font-size: 14px;
    }
    QCalendarWidget QWidget {
        font-size: 14px;
    }
"""

FLOATING_SUBJECT_STYLE = """
    QPushButton {
        background-color: rgba(255, 255, 255, 0.95);
        border: 1.2px solid #d1d5db;
        border-radius: 14px;
        padding: 18px;
        font-size: 17px;
        color: #111827;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.08);
        transition: background-color 0.25s ease;
    }
    QPushButton:hover {
        background-color: #f3f4f6;
    }
"""

def get_ai_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

NOTES_FILE = "notes.json"
ASSIGNMENTS_FILE = "assignment_submissions.json"

if os.path.exists(NOTES_FILE):
    try:
        with open(NOTES_FILE, "r") as f:
            SAVED_NOTES = json.load(f)
    except Exception as e:
        SAVED_NOTES = {}
else:
    SAVED_NOTES = {}

if os.path.exists(ASSIGNMENTS_FILE):
    try:
        with open(ASSIGNMENTS_FILE, "r") as f:
            SUBMITTED_ASSIGNMENTS = json.load(f)
    except Exception as e:
        SUBMITTED_ASSIGNMENTS = {}
else:
    SUBMITTED_ASSIGNMENTS = {}

progress_data = {
    "This Week": [
        ("Math Homework", "Graded: 90/100", "green"),
        ("Science Quiz", "Ungraded", "gray"),
        ("English Essay", "Graded: 88/100", "green"),
        ("History Quiz", "Graded: 82/100", "green"),
        ("Biology Lab", "Ungraded", "gray"),
        ("PE Fitness Test", "Graded: 92/100", "green"),
        ("Computer Assignment", "Graded: 85/100", "green")
    ]
}

# ===============================
# Subject Detail Page - enhanced with improved UI and functionality
class SubjectDetailPage(QWidget):
    def __init__(self, subject_name, back_callback):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel(f"{subject_name} Details")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4f46e5;")
        main_layout.addWidget(title)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget::pane { border: none; }")

        section_data = [
            ("Modules", "modules", [
                ("Module 1: Introduction", "Mathematics is the study of numbers, shapes, and patterns."),
                ("Module 2: Advanced Topics", "Covers calculus and problem-solving techniques."),
                ("Module 3: Practice", "Hands-on exercises and practice problems.")
            ], "#6366f1", "#38bdf8"),
            ("Pointers to Review", "pointers", [
                ("Key Formula", "List of formulas you should memorize."),
                ("Important Concepts", "Concepts you must understand."),
                ("Sample Questions", "Example questions for practice.")
            ], "#f43f5e", "#f87171"),
            ("Assignments", "assignments", [
                ("Assignment 1", "Solve exercises on page 34-35."),
                ("Assignment 2", "Group activity about measurements."),
                ("Assignment 3", "Create a math puzzle.")
            ], "#22c55e", "#a3e635")
        ]

        for title_text, category, items, color_start, color_end in section_data:
            section_widget = QWidget()
            section_layout = QVBoxLayout(section_widget)
            section_layout.setSpacing(18)

            for item_title, item_content in items:
                section_frame = QFrame()
                section_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color_start}, stop:1 {color_end});
                        border-radius: 18px;
                        padding: 14px 16px;
                        box-shadow: 2px 4px 9px rgba(0,0,0,0.12);
                    }}
                """)
                item_layout = QVBoxLayout(section_frame)
                item_layout.setSpacing(8)

                item_label = QLabel(f"\u2022 <b>{item_title}:</b> {item_content}")
                item_label.setFont(QFont("Segoe UI", 14))
                item_label.setStyleSheet("color: white;")
                item_label.setWordWrap(True)
                item_layout.addWidget(item_label)

                if category == "modules":
                    ask_ai_btn = QPushButton("Ask AI")
                    ask_ai_btn.setVisible(False)  # Show only when text is selected
                    ask_ai_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    ask_ai_btn.setFixedSize(90, 28)
                    ask_ai_btn.setStyleSheet("background-color: #fff59d; font-size: 12px; font-weight: 600; border-radius: 6px; color: #444;")
                    item_layout.addWidget(ask_ai_btn, alignment=Qt.AlignmentFlag.AlignRight)

                    def maybe_show_ai_btn():
                        if item_label.hasSelectedText():
                            ask_ai_btn.setVisible(True)
                        else:
                            ask_ai_btn.setVisible(False)

                    def ask_ai_action():
                        selected_text = item_label.selectedText()
                        if selected_text:
                            choice, ok = QInputDialog.getItem(
                                self, "Ask AI", f"What would you like to do with:\n“{selected_text}”",
                                ["Explain", "Edit"], editable=False
                            )
                            if ok:
                                try:
                                    prompt = f"{choice} the following text:\n\n{selected_text}"
                                    # Basic loading while waiting for response
                                    msg_wait = QMessageBox(self)
                                    msg_wait.setWindowTitle("AI Response")
                                    msg_wait.setText("Please wait while AI is processing...")
                                    msg_wait.setStandardButtons(QMessageBox.StandardButton.NoButton)
                                    msg_wait.show()

                                    ai_output = get_ai_response(prompt)

                                    msg_wait.close()
                                    QMessageBox.information(self, f"AI {choice}", ai_output)
                                except Exception as e:
                                    QMessageBox.warning(self, "AI Error", f"Something went wrong:\n{e}")

                    item_label.mouseReleaseEvent = lambda event: (maybe_show_ai_btn(), QLabel.mouseReleaseEvent(item_label, event))
                    ask_ai_btn.clicked.connect(ask_ai_action)

                notes_edit = QTextEdit()
                notes_edit.setPlaceholderText("Private comment...")
                notes_edit.setFont(QFont("Segoe UI", 13))
                notes_edit.setFixedHeight(90)
                note_key = f"{title_text}::{item_title}"
                notes_edit.setText(SAVED_NOTES.get(note_key, ""))

                def save_note(note_key=note_key, notes_edit=notes_edit):
                    SAVED_NOTES[note_key] = notes_edit.toPlainText()
                    try:
                        with open(NOTES_FILE, "w") as f:
                            json.dump(SAVED_NOTES, f, indent=2)
                    except Exception:
                        pass

                notes_edit.textChanged.connect(save_note)
                item_layout.addWidget(notes_edit)

                if category == "assignments":
                    assign_key = f"{subject_name}::{item_title}"

                    upload_btn = QPushButton("Upload File")
                    upload_btn.setStyleSheet("""
                        QPushButton {
                            background-color: white;
                            color: #3b82f6;
                            padding-left: 10px;
                            padding-right: 10px;
                            font-weight: 600;
                            border: 1.5px solid #3b82f6;
                            border-radius: 8px;
                        }
                        QPushButton:hover {
                            background-color: #e0e7ff;
                        }
                        QPushButton:disabled {
                            color: #a5b4fc;
                            border-color: #a5b4fc;
                        }
                    """)
                    upload_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

                    view_btn = QPushButton("View Your Work")
                    view_btn.setStyleSheet("""
                        QPushButton {
                            background-color: white;
                            color: #10b981;
                            padding-left: 10px;
                            padding-right: 10px;
                            font-weight: 600;
                            border: 1.5px solid #10b981;
                            border-radius: 8px;
                        }
                        QPushButton:hover {
                            background-color: #d1fae5;
                        }
                        QPushButton:disabled {
                            color: #6ee7b7;
                            border-color: #6ee7b7;
                        }
                    """)
                    view_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

                    def make_upload_handler(assign_key_local, upload_btn_local, view_btn_local):
                        def upload_file():
                            file_path, _ = QFileDialog.getOpenFileName(self, "Upload Assignment", "", "All Files (*)")
                            if file_path:
                                SUBMITTED_ASSIGNMENTS[assign_key_local] = file_path
                                try:
                                    with open(ASSIGNMENTS_FILE, "w") as f:
                                        json.dump(SUBMITTED_ASSIGNMENTS, f, indent=2)
                                except Exception:
                                    pass
                                upload_btn_local.setText("Uploaded \u2714")
                                upload_btn_local.setEnabled(False)
                                view_btn_local.setEnabled(True)
                        return upload_file

                    def make_view_handler(assign_key_local, upload_btn_local, view_btn_local):
                        def view_or_unsubmit():
                            if assign_key_local in SUBMITTED_ASSIGNMENTS:
                                file_path = SUBMITTED_ASSIGNMENTS[assign_key_local]
                                msg_box = QMessageBox()
                                msg_box.setWindowTitle("Submitted File")
                                file_name = os.path.basename(file_path)
                                msg_box.setText(f"Submitted: {file_name}")
                                msg_box.setInformativeText("What do you want to do?")
                                open_btn = msg_box.addButton("Open File", QMessageBox.ButtonRole.AcceptRole)
                                unsubmit_btn = msg_box.addButton("Unsubmit", QMessageBox.ButtonRole.DestructiveRole)
                                msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                                msg_box.exec()

                                clicked = msg_box.clickedButton()
                                if clicked == unsubmit_btn:
                                    del SUBMITTED_ASSIGNMENTS[assign_key_local]
                                    try:
                                        with open(ASSIGNMENTS_FILE, "w") as f:
                                            json.dump(SUBMITTED_ASSIGNMENTS, f, indent=2)
                                    except Exception:
                                        pass
                                    upload_btn_local.setEnabled(True)
                                    upload_btn_local.setText("Upload File")
                                    view_btn_local.setEnabled(False)
                                elif clicked == open_btn:
                                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                        return view_or_unsubmit

                    upload_btn.clicked.connect(make_upload_handler(assign_key, upload_btn, view_btn))
                    view_btn.clicked.connect(make_view_handler(assign_key, upload_btn, view_btn))

                    if assign_key in SUBMITTED_ASSIGNMENTS:
                        upload_btn.setText("Uploaded \u2714")
                        upload_btn.setEnabled(False)
                        view_btn.setEnabled(True)
                    else:
                        view_btn.setEnabled(False)

                    item_layout.addWidget(upload_btn)
                    item_layout.addWidget(view_btn)

                section_layout.addWidget(section_frame)

            tab_widget.addTab(section_widget, title_text)

        main_layout.addWidget(tab_widget)

        back_btn = QPushButton("Back to Class")
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet("padding: 8px; margin-top: 24px; font-size: 14px; font-weight: 600; max-width: 140px; color: #374151; background-color: #e0e7ff; border-radius: 10px;")
        back_btn.clicked.connect(back_callback)
        main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(main_container)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        self.setLayout(layout)


# ===============================
# Settings Page - Improved visuals, spacing, and UX details
class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("\u2699\ufe0f Settings")
        title.setFont(QFont("Segoe UI Semibold", 20))
        title.setStyleSheet("color: #2563eb;")
        layout.addWidget(title)

        # Change password section
        pw_label = QLabel("Change Password")
        pw_label.setFont(QFont("Segoe UI Semibold", 16))
        layout.addWidget(pw_label)

        self.old_pw_layout = QHBoxLayout()
        self.old_pw_layout.setSpacing(6)
        self.old_pw = QLineEdit()
        self.old_pw.setPlaceholderText("Old Password")
        self.old_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_pw.setFont(QFont("Segoe UI", 14))
        self.old_pw_layout.addWidget(self.old_pw)

        self.toggle_old_btn = QPushButton("\ud83d\udc41")
        self.toggle_old_btn.setCheckable(True)
        self.toggle_old_btn.setFixedSize(36,36)
        self.toggle_old_btn.setStyleSheet("font-size: 20px; background-color: transparent; border: none;")
        self.toggle_old_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_old_btn.clicked.connect(lambda: self.toggle_password_visibility(self.old_pw, self.toggle_old_btn))

        self.old_pw_layout.addWidget(self.toggle_old_btn)
        layout.addLayout(self.old_pw_layout)

        self.new_pw_layout = QHBoxLayout()
        self.new_pw_layout.setSpacing(6)
        self.new_pw = QLineEdit()
        self.new_pw.setPlaceholderText("New Password")
        self.new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pw.setFont(QFont("Segoe UI", 14))
        self.new_pw_layout.addWidget(self.new_pw)

        self.toggle_new_btn = QPushButton("\ud83d\udc41")
        self.toggle_new_btn.setCheckable(True)
        self.toggle_new_btn.setFixedSize(36,36)
        self.toggle_new_btn.setStyleSheet("font-size: 20px; background-color: transparent; border: none;")
        self.toggle_new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_new_btn.clicked.connect(lambda: self.toggle_password_visibility(self.new_pw, self.toggle_new_btn))

        self.new_pw_layout.addWidget(self.toggle_new_btn)
        layout.addLayout(self.new_pw_layout)

        change_pw_btn = QPushButton("Update Password")
        change_pw_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        change_pw_btn.setStyleSheet("background-color: #4ade80; color: white; padding: 14px; border-radius: 12px; font-size: 16px; font-weight: 700;")
        change_pw_btn.clicked.connect(self.update_password)
        layout.addWidget(change_pw_btn)

        # Notification preferences section
        notif_label = QLabel("Notification Preferences")
        notif_label.setFont(QFont("Segoe UI Semibold", 16))
        notif_label.setContentsMargins(0, 24, 0, 6)
        layout.addWidget(notif_label)

        self.notif_checkbox = QCheckBox("Enable Email Notifications")
        self.notif_checkbox.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.notif_checkbox)

        save_btn = QPushButton("Save Settings")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet("background-color: #60a5fa; color: white; padding: 14px; border-radius: 12px; font-size: 16px; font-weight: 700;")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        self.setLayout(layout)

    def toggle_password_visibility(self, line_edit, button):
        if button.isChecked():
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def update_password(self):
        old_pw = self.old_pw.text()
        new_pw = self.new_pw.text()
        if old_pw and new_pw:
            # Here, add real password change logic if needed
            QMessageBox.information(self, "Success", "Password updated successfully.")
            self.old_pw.clear()
            self.new_pw.clear()
        else:
            QMessageBox.warning(self, "Input Required", "Please fill both password fields.")

    def save_settings(self):
        status = self.notif_checkbox.isChecked()
        # Here, add real settings persistence logic if needed
        QMessageBox.information(self, "Settings", f"Settings saved.\nEmail Notifications: {'Enabled' if status else 'Disabled'}")


# ===============================
# Student Dashboard - Enhanced UI, consistency, and interaction improvements
class StudentDashboard(QWidget):
    def __init__(self, go_back_callback):
        super().__init__()
        self.setWindowTitle("Student Panel - StudySync")
        self.setMinimumSize(980, 640)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("background-color: #f3f4f6; border-right: 1.5px solid #e5e7eb;")
        self.sidebar = QVBoxLayout(sidebar_widget)
        self.sidebar.setContentsMargins(25, 25, 25, 25)
        self.sidebar.setSpacing(24)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedHeight(120)
        logo_label.setText("<div align='center' style='line-height:1.2; font-size: 28px; color: #3b82f6;'>\U0001F393<br><b>StudySync</b></div>")
        logo_label.setTextFormat(Qt.TextFormat.RichText)
        logo_label.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        self.sidebar.addWidget(logo_label)

        self.buttons = {}
        btn_names = ["Dashboard", "Class", "Calendar", "Progress", "Setting"]
        for name in btn_names:
            btn = QPushButton(name)
            btn.setFont(QFont("Segoe UI", 14))
            btn.setFixedHeight(52)
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding-left: 14px;
                    color: #4b5563;
                    text-align: left;
                    font-weight: 600;
                    border-radius: 12px;
                    transition: background-color 0.3s ease, color 0.3s ease;
                }
                QPushButton:hover {
                    background-color: #e0e7ff;
                    color: #4338ca;
                }
                QPushButton:checked {
                    background-color: #4338ca;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, n=name: self.display_page(n))
            self.sidebar.addWidget(btn)
            self.buttons[name] = btn

        self.sidebar.addStretch()
        back_btn = QPushButton("Back")
        back_btn.setFont(QFont("Segoe UI", 14))
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f87171;
                color: white;
                padding: 12px;
                border-radius: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        back_btn.clicked.connect(go_back_callback)
        self.sidebar.addWidget(back_btn)

        # Content Area
        self.content_area = QStackedWidget()
        self.pages = {
            "Dashboard": self.create_dashboard_overview(),
            "Class": self.create_class_page(),
            "Calendar": self.create_calendar_page(),
            "Progress": self.create_progress_page(),
            "Setting": SettingsPage()
        }
        for name, widget in self.pages.items():
            if isinstance(widget, QLabel):
                widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                widget.setFont(QFont("Segoe UI", 16))
            self.content_area.addWidget(widget)

        sidebar_widget.setFixedWidth(220)
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.content_area)

        self.setLayout(main_layout)
        self.display_page("Dashboard")

    def create_dashboard_overview(self):
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(28)

        # Left side: Calendar + Graph
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)

        calendar_label = QLabel("\U0001F4C5 Calendar Preview")
        calendar_label.setFont(QFont("Segoe UI Semibold", 16))
        calendar_label.setStyleSheet("color: #1e40af;")
        left_layout.addWidget(calendar_label)

        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.setFixedHeight(240)
        calendar.setFont(QFont("Segoe UI", 13))
        calendar.setStyleSheet("""
            QCalendarWidget QWidget { font-size: 14px; }
            QCalendarWidget QToolButton { height:30px; font-weight: 600; color: #2563eb; }
            QCalendarWidget QAbstractItemView:enabled { font-weight: 600; }
            QCalendarWidget QAbstractItemView:enabled:selected { background-color: #3b82f6; color: white; border-radius: 6px; }
        """)
        left_layout.addWidget(calendar)

        graph_label = QLabel("\n\U0001F4C8 Weekly Score Snapshot")
        graph_label.setFont(QFont("Segoe UI Semibold", 16))
        graph_label.setStyleSheet("color: #1e40af;")
        left_layout.addWidget(graph_label)

        fig = Figure(figsize=(6, 3), dpi=120)
        graph_canvas = FigureCanvas(fig)
        graph_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        graph_canvas.setMinimumHeight(220)
        left_layout.addWidget(graph_canvas)

        ax = fig.add_subplot(111)

        key = "This Week"
        subjects = [item[0] for item in progress_data[key]]
        scores = [int(item[1].split(": ")[1].split("/")[0]) if "Graded" in item[1] else 0 for item in progress_data[key]]

        ax.plot(subjects, scores, marker='o', color="#2563eb", linewidth=2)
        ax.fill_between(subjects, scores, color="#93c5fd", alpha=0.3)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Score", fontsize=10, color="#1e40af")
        ax.set_title(f"{key} Scores", fontsize=12, color="#1e40af", weight='bold')
        ax.tick_params(axis='x', labelsize=8, rotation=15, colors="#4b5563")
        ax.tick_params(axis='y', labelsize=9, colors="#4b5563")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#60a5fa')
        ax.spines['bottom'].set_color('#60a5fa')

        ax.grid(True, linestyle='--', alpha=0.25)

        # Right side: Tasklists and Notifications
        right_layout = QVBoxLayout()
        right_layout.setSpacing(18)

        task_label = QLabel("\ud83d\udccc Today's Tasks")
        task_label.setFont(QFont("Segoe UI Semibold", 16))
        task_label.setStyleSheet("color: #2563eb;")
        right_layout.addWidget(task_label)

        task_list = QListWidget()
        task_list.setStyleSheet("""
            QListWidget { font-size: 15px; border-radius: 10px; padding: 8px; }
            QListWidget::item { padding: 8px 12px; }
            QListWidget::item:selected { background-color: #bfdbfe; color: #1e40af; }
        """)
        task_list.addItems(["Math Quiz - 10:00 AM", "Science Lab - 2:00 PM"])
        right_layout.addWidget(task_list)

        upcoming_label = QLabel("\u23f3 Upcoming Activities")
        upcoming_label.setFont(QFont("Segoe UI Semibold", 16))
        upcoming_label.setStyleSheet("color: #2563eb; margin-top: 12px;")
        right_layout.addWidget(upcoming_label)

        upcoming_list = QListWidget()
        upcoming_list.setStyleSheet(task_list.styleSheet())
        upcoming_list.addItems(["Essay Due - June 20", "History Exam - June 22"])
        right_layout.addWidget(upcoming_list)

        notif_label = QLabel("\ud83d\udce2 Teacher Posts & Announcements")
        notif_label.setFont(QFont("Segoe UI Semibold", 16))
        notif_label.setStyleSheet("color: #2563eb; margin-top: 12px;")
        right_layout.addWidget(notif_label)

        notif_list = QListWidget()
        notif_list.setStyleSheet(task_list.styleSheet())
        notif_list.addItems(["New Announcement: Review for Final Exam", "Reminder: Submit Science Project"])
        right_layout.addWidget(notif_list)

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 2)

        return widget

    def create_class_page(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(24)
        layout.setContentsMargins(28, 28, 28, 28)

        subjects = [
            ("Mathematics", "\ud83d\udcd0", "#fce7f3"),
            ("Science", "\ud83d\udd2c", "#dbeafe"),
            ("English", "\ud83d\udcda", "#fee2e2"),
            ("History", "\ud83c\udff0", "#e0f2fe"),
            ("Geography", "\ud83d\uddfa\ufe0f", "#dcfce7"),
            ("Computer Science", "\ud83d\udcbb", "#ede9fe"),
            ("Art", "\ud83c\udfa8", "#fef9c3")
        ]

        for subject, icon, color in subjects:
            box = QPushButton(f"{icon}  {subject}")
            box.setFixedHeight(90)
            box.setFont(QFont("Segoe UI Semibold", 17))
            box.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 1.3px solid #ccc;
                    border-radius: 16px;
                    padding: 18px;
                    color: #111827;
                    transition: background-color 0.3s ease;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: #e5e7eb;
                }}
            """)
            box.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            box.clicked.connect(lambda _, s=subject: self.show_subject_detail(s))
            layout.addWidget(box)

        layout.addStretch()
        scroll_area.setWidget(container)
        return scroll_area

    def show_subject_detail(self, subject_name):
        detail_page = self.create_subject_detail_page(subject_name)
        self.pages["SubjectDetail"] = detail_page
        self.content_area.addWidget(detail_page)
        self.content_area.setCurrentWidget(detail_page)
        for btn in self.buttons.values():
            btn.setChecked(False)

    def create_subject_detail_page(self, subject_name):
        return SubjectDetailPage(subject_name, self.back_to_class)

    def back_to_class(self):
        self.display_page("Class")

    def create_calendar_page(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("\U0001F4C5 Calendar & Task Schedule")
        title.setFont(QFont("Segoe UI Semibold", 20))
        title.setStyleSheet("color: #2563eb;")
        main_layout.addWidget(title)

        split_layout = QHBoxLayout()
        split_layout.setSpacing(32)

        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.setFont(QFont("Segoe UI", 14))
        calendar.setFixedWidth(370)
        calendar.setStyleSheet("""
            QCalendarWidget QWidget { font-size: 14px; }
            QCalendarWidget QToolButton { height:34px; font-weight: 600; color: #2563eb; }
            QCalendarWidget QAbstractItemView:enabled:selected { background-color: #3b82f6; color: white; border-radius: 8px; }
        """)
        split_layout.addWidget(calendar)

        today_box = QVBoxLayout()
        today_label = QLabel("To-do")
        today_label.setFont(QFont("Segoe UI Semibold", 18))
        today_label.setStyleSheet("color: #2563eb;")
        today_box.addWidget(today_label)

        self.today_list = QListWidget()
        self.today_list.setStyleSheet("""
            QListWidget { font-size: 15px; border-radius: 10px; padding: 10px; }
            QListWidget::item { padding: 10px 14px; }
            QListWidget::item:selected { background-color: #bfdbfe; color: #1e40af; }
        """)
        today_box.addWidget(self.today_list)

        add_task_btn = QPushButton("\u2795 New To-do")
        add_task_btn.setFont(QFont("Segoe UI Semibold", 13))
        add_task_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #4ade80;
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-weight: 700;
                max-width: 120px;
                margin-top: 12px;
            }
            QPushButton:hover {
                background-color: #22c55e;
            }
            QPushButton:pressed {
                background-color: #16a34a;
            }
        """)

        def add_task():
            text, ok = QInputDialog.getText(widget, "Add Task", "Enter task for today:")
            if ok and text.strip():
                self.today_list.addItem(text.strip())

        add_task_btn.clicked.connect(add_task)
        today_box.addWidget(add_task_btn)
        today_box.addStretch()
        split_layout.addLayout(today_box)

        main_layout.addLayout(split_layout)

        upcoming_label = QLabel("Incoming Activities")
        upcoming_label.setFont(QFont("Segoe UI Semibold", 18))
        upcoming_label.setStyleSheet("color: #2563eb; margin-top: 18px;")
        main_layout.addWidget(upcoming_label)

        self.upcoming_list = QListWidget()
        self.upcoming_list.setStyleSheet(self.today_list.styleSheet())
        main_layout.addWidget(self.upcoming_list)

        # Mock data for calendar page task lists
        self.today_list.addItems(["Math Quiz - 10:00 AM", "Science Lab - 2:00 PM"])
        self.upcoming_list.addItems(["Essay Due - June 20", "History Exam - June 22"])

        return widget

    def create_progress_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        title = QLabel("\U0001F4CA Progress Tracker")
        title.setFont(QFont("Segoe UI Semibold", 20))
        title.setStyleSheet("color: #2563eb;")
        layout.addWidget(title)

        # Progress data extended here for reference
        progress = {
            "This Week": [
                ("Math Homework", "Graded: 90/100", "green"),
                ("Science Quiz", "Ungraded", "gray"),
                ("English Essay", "Graded: 88/100", "green"),
                ("History Quiz", "Graded: 82/100", "green"),
                ("Biology Lab", "Ungraded", "gray"),
                ("PE Fitness Test", "Graded: 92/100", "green"),
                ("Computer Assignment", "Graded: 85/100", "green")
            ],
            "Last Week": [
                ("Math Project", "Graded: 87/100", "green"),
                ("Science Lab", "Ungraded", "gray"),
                ("English Reading", "Graded: 80/100", "green"),
                ("History Report", "Graded: 78/100", "green"),
                ("Art Sketch", "Ungraded", "gray"),
                ("Geography Quiz", "Graded: 84/100", "green"),
                ("Music Composition", "Graded: 90/100", "green")
            ],
            "Last Month": [
                ("Math Exam", "Graded: 75/100", "green"),
                ("Science Fair", "Graded: 93/100", "green"),
                ("English Portfolio", "Ungraded", "gray"),
                ("History Debate", "Graded: 85/100", "green"),
                ("Computer Lab", "Graded: 80/100", "green"),
                ("Art Exhibit", "Ungraded", "gray"),
                ("Geography Map", "Graded: 86/100", "green")
            ]
        }

        FigureCanvas(Figure()).figure.subplots().tick_params(axis='x', labelsize=5)

        self.dropdown = QComboBox()
        self.dropdown.setFont(QFont("Segoe UI", 14))
        self.dropdown.addItems(progress.keys())
        self.dropdown.setCurrentText("This Week")
        layout.addWidget(self.dropdown)

        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget { font-size: 15px; border-radius: 10px; padding: 10px; }
            QListWidget::item { padding: 10px 14px; }
        """)
        layout.addWidget(self.activity_list)

        graph_title = QLabel("\n\ud83d\udcc8 Performance Trend")
        graph_title.setFont(QFont("Segoe UI Semibold", 18))
        graph_title.setStyleSheet("color: #2563eb;")
        layout.addWidget(graph_title)

        self.canvas = FigureCanvas(Figure(figsize=(6, 2.5), dpi=120))
        layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.add_subplot(111)

        def update_graph(filter_key):
            self.ax.clear()
            subjects = [s[0] for s in progress[filter_key]]
            scores = []
            for item in progress[filter_key]:
                if "Graded" in item[1]:
                    score = int(item[1].split(": ")[1].split("/")[0])
                else:
                    score = 0
                scores.append(score)
            self.ax.plot(subjects, scores, marker='o', linestyle='-', color="#2563eb", linewidth=2)
            self.ax.fill_between(subjects, scores, color="#93c5fd", alpha=0.3)
            self.ax.tick_params(axis='x', labelsize=8, rotation=15, colors='#4b5563')
            self.ax.tick_params(axis='y', labelsize=9, colors='#4b5563')
            self.ax.set_ylim(0, 100)
            self.ax.set_ylabel("Score", fontsize=11, color="#1e40af")
            self.ax.set_title(f"{filter_key} Scores", fontsize=14, color="#1e40af", weight='bold')
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color('#60a5fa')
            self.ax.spines['bottom'].set_color('#60a5fa')

            self.ax.grid(True, linestyle='--', alpha=0.25)
            self.canvas.draw()

        def update_activity_list():
            self.activity_list.clear()
            selected = self.dropdown.currentText()
            for subject, status, color in progress[selected]:
                item = QListWidgetItem(f"{subject} - {status}")
                item.setForeground(QColor(color))
                self.activity_list.addItem(item)
            update_graph(selected)

        self.dropdown.currentTextChanged.connect(update_activity_list)
        update_activity_list()

        layout.addStretch()
        return widget

    def display_page(self, page_name):
        if page_name not in self.pages:
            return
        index = list(self.pages.keys()).index(page_name)
        self.content_area.setCurrentIndex(index)
        for name, btn in self.buttons.items():
            btn.setChecked(name == page_name)


# ===============================
# Welcome Window (Improved UI with animations and polished look)
class WelcomeWindow(QWidget):
    def __init__(self, student_no, continue_callback):
        super().__init__()
        self.student_no = student_no
        self.continue_callback = continue_callback
        self.setWindowTitle("Welcome")
        self.setFixedSize(450, 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
        self.setup_ui()
        self.init_animation()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        icon_label = QLabel("\U0001F44B")  # Waving Hand emoji
        icon_label.setFont(QFont("Segoe UI Emoji", 60))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        welcome_label = QLabel()
        welcome_label.setText(f"""<h1 style="color: qlineargradient(
            spread:pad, x1:0, y1:0, x2:1, y2:0, 
            stop:0 #3366ff, stop:1 #6fb1fc); font-weight:bold;">
            Welcome!</h1>""")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(welcome_label)

        student_label = QLabel(f"Student Number: <b>{self.student_no}</b>")
        student_label.setFont(QFont("Segoe UI", 16))
        student_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        student_label.setStyleSheet("color: #555555;")
        layout.addWidget(student_label)

        note_label = QLabel("You have successfully logged in.\nEnjoy your session!")
        note_label.setFont(QFont("Segoe UI", 13))
        note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note_label.setStyleSheet("color: #666666;")
        layout.addWidget(note_label)

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setFont(QFont("Segoe UI", 14))
        self.continue_btn.setFixedHeight(45)
        self.continue_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #3366ff;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 600;
                transition-duration: 200ms;
            }
            QPushButton:hover {
                background-color: #254eda;
            }
            QPushButton:pressed {
                background-color: #1a3bb8;
            }
        """)
        self.continue_btn.clicked.connect(self.continue_callback)
        layout.addWidget(self.continue_btn)

        layout.addStretch()
        self.setLayout(layout)

    def init_animation(self):
        self.setWindowOpacity(0.0)
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(700)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def showEvent(self, event):
        self.animation.start()
        super().showEvent(event)


# ===============================
# Login Window - updated for consistency and polished styling
class LoginWindow(QWidget):
    def __init__(self, role, on_login_callback, go_back_callback):
        super().__init__()
        self.setWindowTitle(f"{role} Login")
        self.setFixedSize(420, 320)
        self.role = role
        self.on_login_callback = on_login_callback
        self.go_back_callback = go_back_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(18)

        title_label = QLabel("Study <b style='color:#3366ff;'>Sync</b>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI Semibold", 26))
        title_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(title_label)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText(f"{self.role} No.")
        self.id_input.setFont(QFont("Segoe UI", 14))
        self.id_input.setFixedHeight(38)
        layout.addWidget(self.id_input)

        self.password_layout = QHBoxLayout()
        self.password_layout.setSpacing(8)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Segoe UI", 14))
        self.password_input.setFixedHeight(38)

        self.toggle_pw_btn = QPushButton("\ud83d\udc41")
        self.toggle_pw_btn.setCheckable(True)
        self.toggle_pw_btn.setFixedSize(40, 40)
        self.toggle_pw_btn.setStyleSheet("font-size: 18px; background-color: transparent; border: none;")
        self.toggle_pw_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_pw_btn.clicked.connect(self.toggle_password_visibility)

        self.password_layout.addWidget(self.password_input)
        self.password_layout.addWidget(self.toggle_pw_btn)
        layout.addLayout(self.password_layout)

        options_layout = QHBoxLayout()
        self.remember_checkbox = QCheckBox("Remember me?")
        self.remember_checkbox.setFont(QFont("Segoe UI", 13))
        options_layout.addWidget(self.remember_checkbox)

        options_layout.addStretch()

        self.forgot_label = QLabel("<a href='#'>Forgot password?</a>")
        self.forgot_label.setFont(QFont("Segoe UI", 13))
        self.forgot_label.setTextFormat(Qt.TextFormat.RichText)
        self.forgot_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.forgot_label.setOpenExternalLinks(True)
        options_layout.addWidget(self.forgot_label)

        layout.addLayout(options_layout)

        login_btn = QPushButton("Login")
        login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        login_btn.setFont(QFont("Segoe UI Semibold", 16))
        login_btn.setFixedHeight(48)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        back_btn = QPushButton("Back")
        back_btn.setFont(QFont("Segoe UI", 14))
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f87171;
                color: white;
                border-radius: 12px;
                padding: 10px 0;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        back_btn.setFixedHeight(40)
        back_btn.clicked.connect(self.go_back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def toggle_password_visibility(self):
        if self.toggle_pw_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def handle_login(self):
        student_no = self.id_input.text().strip()

        if self.role == "Student":
            if not re.fullmatch(r"\d{2}-\d{5}", student_no):
                QMessageBox.warning(
                    self, "Invalid Student Number",
                    "Please enter a valid student number (e.g., 22-XXXXX)."
                )
                return

        if student_no and self.password_input.text().strip():
            # Show WelcomeWindow before dashboard
            self.welcome_window = WelcomeWindow(student_no, self.proceed_to_dashboard)
            self.welcome_window.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Input Required", "Please enter both ID and password.")

    def proceed_to_dashboard(self):
        self.welcome_window.close()
        self.on_login_callback(self.role)
        self.close()


# ===============================
# ProfessorWindow placeholder (as referenced)
class ProfessorWindow(QWidget):
    def __init__(self, go_back_callback):
        super().__init__()
        self.setWindowTitle("Professor Panel")
        self.setMinimumSize(800, 500)
        layout = QVBoxLayout()
        label = QLabel("Professor Dashboard coming soon...")
        label.setFont(QFont("Segoe UI Semibold", 20))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        back_btn = QPushButton("Back")
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setFixedWidth(120)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f87171;
                color: white;
                border-radius: 12px;
                padding: 10px 0;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        back_btn.clicked.connect(go_back_callback)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)


# ===============================
# Main Window with refined UI and buttons
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudySync")
        self.setFixedSize(900, 540)
        self.setup_ui()

    def setup_ui(self):
        title = QLabel("Study <b style='color:#3366ff;'>Sync.</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI Semibold", 36))
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setContentsMargins(0, 0, 0, 40)

        professor_btn = self.create_role_button("Professor", "\U0001F9D1\u200D\U0001F3EB", self.open_professor_login)
        student_btn = self.create_role_button("Student", "\U0001F393", self.open_student_login)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(professor_btn)
        button_layout.addSpacing(60)
        button_layout.addWidget(student_btn)
        button_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(title)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        main_layout.setContentsMargins(40, 40, 40, 40)

        self.setLayout(main_layout)

    def create_role_button(self, label, icon_text, callback):
        btn = QPushButton(f"{icon_text}\n{label}")
        btn.setFont(QFont("Segoe UI Semibold", 20))
        btn.setFixedSize(230, 230)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 30px;
                border: 2px solid transparent;
                padding: 30px;
                color: #374151;
                font-weight: 700;
                letter-spacing: 0.8px;
                transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
            }
            QPushButton:hover {
                background-color: rgba(240, 240, 240, 0.95);
                border-color: #3366ff;
                color: #1e40af;
            }
            QPushButton:pressed {
                background-color: #dbeafe;
                border-color: #3b82f6;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(4, 4)
        btn.setGraphicsEffect(shadow)
        btn.clicked.connect(callback)
        return btn

    def open_professor_login(self):
        self.login_window = LoginWindow("Professor", self.show_dashboard, self.show_main)
        self.login_window.show()
        self.hide()

    def open_student_login(self):
        self.login_window = LoginWindow("Student", self.show_dashboard, self.show_main)
        self.login_window.show()
        self.hide()

    def show_dashboard(self, role):
        if role == "Professor":
            self.dashboard = ProfessorWindow(self.show_main)
        else:
            self.dashboard = StudentDashboard(self.show_main)
        self.dashboard.show()
        self.login_window.close()

    def show_main(self):
        self.show()
        if hasattr(self, 'login_window'):
            self.login_window.close()
        if hasattr(self, 'dashboard'):
            self.dashboard.close()


# ===============================
# Run Application with stylesheet applied

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Fusion style for consistency across platforms
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())