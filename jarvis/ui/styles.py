"""Dark futuristic theme — black / dark-blue with cyan accents."""

THEME = {
    "bg": "#050a14",
    "bg_panel": "#0a1628",
    "bg_input": "#0d1b2a",
    "border": "#1b3a5a",
    "cyan": "#00e5ff",
    "cyan_dim": "#0088aa",
    "text": "#e6f7ff",
    "text_dim": "#7a9bb5",
    "danger": "#ff3366",
    "ok": "#00ff9d",
    "warn": "#ffcc00",
}

STYLESHEET = f"""
QWidget {{
    background-color: {THEME['bg']};
    color: {THEME['text']};
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
}}
QMainWindow, QDialog {{
    background-color: {THEME['bg']};
}}
QFrame#panel {{
    background-color: {THEME['bg_panel']};
    border: 1px solid {THEME['border']};
    border-radius: 8px;
}}
QLabel#brand {{
    color: {THEME['cyan']};
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 4px;
}}
QLabel#sectionTitle {{
    color: {THEME['cyan']};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QLabel#statusDim {{
    color: {THEME['text_dim']};
    font-size: 11px;
}}
QTextEdit, QPlainTextEdit, QLineEdit, QListWidget, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {THEME['bg_input']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    padding: 6px;
    selection-background-color: {THEME['cyan_dim']};
}}
QPushButton {{
    background-color: {THEME['bg_panel']};
    border: 1px solid {THEME['cyan_dim']};
    border-radius: 6px;
    padding: 8px 14px;
    color: {THEME['cyan']};
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #102a40;
    border-color: {THEME['cyan']};
}}
QPushButton:pressed {{
    background-color: #061018;
}}
QPushButton#primary {{
    background-color: #003344;
    border: 1px solid {THEME['cyan']};
}}
QPushButton#danger {{
    color: {THEME['danger']};
    border-color: {THEME['danger']};
    font-weight: 800;
    letter-spacing: 1px;
}}
QPushButton#danger:hover {{
    background-color: #2a0a14;
}}
QPushButton#micActive {{
    background-color: #003322;
    border-color: {THEME['ok']};
    color: {THEME['ok']};
}}
QScrollBar:vertical {{
    background: {THEME['bg']};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {THEME['cyan_dim']};
    border-radius: 4px;
    min-height: 24px;
}}
QCheckBox, QGroupBox {{
    color: {THEME['text']};
}}
QGroupBox {{
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    color: {THEME['cyan']};
}}
QTabWidget::pane {{
    border: 1px solid {THEME['border']};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: {THEME['bg_panel']};
    color: {THEME['text_dim']};
    padding: 8px 16px;
    border: 1px solid {THEME['border']};
}}
QTabBar::tab:selected {{
    color: {THEME['cyan']};
    border-bottom-color: {THEME['cyan']};
}}
QStatusBar {{
    background: {THEME['bg_panel']};
    color: {THEME['text_dim']};
}}
"""
