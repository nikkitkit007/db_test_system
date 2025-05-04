style_sheet = """
/* ================ ОБЩИЙ ФОН MAINWINDOW ================ */
QMainWindow {
    background-color: #f2f2f2;
    color: #333333;
    font-family: Arial, sans-serif;
    font-size: 14px;
}

/* ================ TAB WIDGET И ТАБЫ ================ */
QTabWidget::pane {
    border: 1px solid #aaa;
    background-color: #ffffff;
}

QTabBar::tab {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #e6e6e6,
        stop: 1 #dcdcdc
    );
    border: 1px solid #ccc;
    padding: 10px;
    min-width: 140px;
    font-size: 14px;
    margin-right: 1px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #c0d0ff,
        stop: 1 #b0c0ff
    );
    font-weight: bold;
    border-bottom: 2px solid #5a7dff;
    margin-bottom: -1px; /* Подчёркиваем выбранную вкладку */
}

QTabBar::tab:hover {
    background: #d0e0ff;
}

/* ================ БАЗОВЫЕ НАСТРОЙКИ ВСЕХ WIDGET-ОВ ================ */
QWidget {
    color: #333333;
    font-family: Arial, sans-serif;
    font-size: 14px;
}

/* ================ GROUPBOX (рамка + заголовок) ================ */
QGroupBox {
    border: 1px solid #ccc;
    border-radius: 5px;
    margin-top: 2ex; /* отступ для заголовка */
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    background-color: transparent;
    font-weight: bold;
    color: #000000;
    font-size: 15px;
}

/* ================ LABEL (заголовки, подписи) ================ */
QLabel {
    font-size: 15px;
    color: #000000;
}

/* ================ PUSH BUTTON ================ */
QPushButton {
    background-color: #4CAF50;
    color: #ffffff;
    border: 1px solid #3e8e41;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #45a049;
}

QPushButton:pressed {
    background-color: #3e8e41;
}

/* ================ LINE EDIT, SPIN BOX, COMBO BOX ================ */
QLineEdit,
QSpinBox,
QComboBox {
    border: 1px solid #ccc;
    border-radius: 3px;
    padding: 5px;
    background-color: #ffffff;
    selection-background-color: #c0d0ff; /* Цвет выделенного текста */
}

/* ================ TABLE WIDGET ================ */
QTableWidget {
    gridline-color: #cccccc;
    border: 1px solid #ccc;
    background-color: #ffffff;
    selection-background-color: #c0d0ff;
}

QTableWidget QHeaderView::section {
    background-color: #e0e0e0;
    border: 1px solid #ccc;
    padding: 5px;
    font-weight: bold;
}

/* ================ LIST WIDGET ================ */
QListWidget {
    border: 1px solid #ccc;
    background-color: #ffffff;
    selection-background-color: #c0d0ff;
}

/* ================ SIDEBAR / TREEWIDGET ================ */
#sidebar {
    background-color: #2E2E2E; /* Тёмно-серый */
    /* Можно чуть светлее: #3C3C3C, чтобы был виден контраст для чёрных иконок */
}

QTreeWidget {
    background-color: #2E2E2E;
    color: #FFFFFF;
    border: none;
}

QTreeWidget::item:hover {
    background-color: #6F8AA9;
}

QTreeWidget::item:selected {
    background-color: #6F8AA9; /* Цвет выделения, например, синий */
    color: #ffffff;            /* Цвет текста при выделении */
}

/* ================ TOOL BUTTON (иконки в sidebar, к примеру) ================ */
QToolButton {
    color: #FFFFFF;               /* Текст и иконки будут белыми, если это SVG со стилями */
    background-color: #2E2E2E;
    border: none;
    padding: 8px;
    font-size: 14px;
}

QToolButton:hover {
    background-color: #505050;
}

/* ================ TOOLTIP ================ */
QToolTip {
    background-color: #fefefe;
    color: #333333;
    border: 1px solid #aaaaaa;
    padding: 4px;
    font-size: 12px;
}
"""
lang_button_style = """
    QToolButton {
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 4px 8px;
    }
    QToolButton:checked {
        background-color: #007bff;
        color: white;
        border: 1px solid #0056b3;
    }
    QToolButton:hover {
        border: 1px solid #0056b3;
    }
"""
