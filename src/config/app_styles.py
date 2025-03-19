style_sheet = """
QMainWindow {
    background-color: #f9f9f9;
}

QTabWidget::pane {
    border: 1px solid #aaa;
    background-color: #ffffff;
}

QTabBar::tab {
    background: #e0e0e0;
    border: 1px solid #ccc;
    padding: 10px;
    min-width: 150px;
    font-family: Arial;
    font-size: 14px;
}

QTabBar::tab:selected {
    background: #c0d0ff;
    font-weight: bold;
    border-bottom: 2px solid #5a7dff;
}

QTabBar::tab:hover {
    background: #d0e0ff;
}

QWidget {
    font-family: Arial;
    font-size: 14px;
    color: #333333;
}

QLabel {
    font-size: 16px;
    font-weight: bold;
    color: #000000;
}

QPushButton {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 5px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #45a049;
}

QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #ccc;
    border-radius: 3px;
    padding: 5px;
    background-color: #ffffff;
}

QTableWidget {
    gridline-color: #cccccc;
    border: 1px solid #ccc;
    background-color: #f9f9f9;
}

QTableWidget QHeaderView::section {
    background-color: #e0e0e0;
    border: 1px solid #ccc;
    padding: 5px;
    font-weight: bold;
}

QListWidget {
    border: 1px solid #ccc;
    background-color: #ffffff;
}
#sidebar {
            background-color: #2e2e2e;
        }
        QTreeWidget {
            background-color: #2e2e2e;
            color: white;
            border: none;
        }
        QTreeWidget::item:hover {
            background-color: #505050;
        }
        QToolButton {
            color: white;
            background-color: #2e2e2e;
            border: none;
            padding: 8px;
        }
        QToolButton:hover {
            background-color: #505050;
        }
"""
