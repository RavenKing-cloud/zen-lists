import os
import json
from PyQt5 import QtWidgets, QtGui, QtCore

# Get the directory of the Python script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the relative path to the todo.json file
todo_json_path = os.path.join(script_dir, "data", 'todo.json')

# Function to load the JSON data
def load_json():
    with open(todo_json_path, 'r') as f:
        return json.load(f)

# Function to update the JSON file
def update_json():
    with open(todo_json_path, 'w') as f:
        json.dump(todo_data, f, indent=4)

# Load the initial JSON data
todo_data = load_json()

class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Highlight)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a custom font
        font = QtGui.QFont("Consolas", 10)
        bold_font = QtGui.QFont("Pristina", 16, QtGui.QFont.Bold)

        # Title label with bold font
        self.title = QtWidgets.QLabel("ZenTodo - Editor", self)
        self.title.setFont(bold_font)
        self.title.setStyleSheet("color: lightgreen;")
        
        # Minimize button with custom font and color
        self.btn_minimize = QtWidgets.QPushButton("-", self)
        self.btn_minimize.setFont(font)
        self.btn_minimize.setFixedSize(25, 25)
        self.btn_minimize.setStyleSheet("background-color: orange; color: black;")
        self.btn_minimize.clicked.connect(parent.showMinimized)
        
        # Close button with custom font and color
        self.btn_close = QtWidgets.QPushButton("X", self)
        self.btn_close.setFont(font)
        self.btn_close.setFixedSize(35, 25)
        self.btn_close.setStyleSheet("background-color: red; color: black;")
        self.btn_close.clicked.connect(parent.close)

        layout.addWidget(self.title)
        layout.addStretch(1)
        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_close)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPos() - self.old_pos)
        self.parent().move(self.parent().x() + delta.x(), self.parent().y() + delta.y())
        self.old_pos = event.globalPos()

# Define colors for priority levels
priority_colors = {
    10: QtGui.QColor(230, 0, 0),       # red
    9: QtGui.QColor(255, 75, 0),       # redorange
    8: QtGui.QColor(255, 150, 50),     # orange
    7: QtGui.QColor(255, 200, 0),      # yelloworange
    6: QtGui.QColor(255, 255, 0),      # yellow
    5: QtGui.QColor(200, 255, 0),      # white
    4: QtGui.QColor(125, 255, 0),      # grey blue
    3: QtGui.QColor(60, 240, 0),       # bluewhite
    2: QtGui.QColor(0, 220, 20),        # brightblue
    1: QtGui.QColor(0, 200, 75)        # green
}

class TodoList(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setMinimumSize(800, 600)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setStyleSheet("background-color: black;")
        layout.addWidget(self.title_bar)

        # Create a toolbar
        self.toolbar = QtWidgets.QToolBar("Main Toolbar")
        layout.addWidget(self.toolbar)

        # Add actions to the toolbar
        create_action = QtWidgets.QAction("Create Todo", self)
        create_action.triggered.connect(self.create_todo)  # Connect to create_todo method
        self.toolbar.addAction(create_action)

        clear_completed_action = QtWidgets.QAction("Clear Completed", self)
        clear_completed_action.triggered.connect(self.clear_completed_todos)
        self.toolbar.addAction(clear_completed_action)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Text", "Priority", "Completed"])
        layout.addWidget(self.table)

        # Set column widths
        table_width = self.table.width()
        self.table.setColumnWidth(0, table_width // 2)   # Text column takes up half of the window
        self.table.setColumnWidth(1, table_width // 4)   # Priority column takes up a quarter
        self.table.setColumnWidth(2, table_width // 4)   # Completed column takes up a quarter

        # Set stretch factors
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

        self.render_todos()

        # Apply custom font to the table
        font = QtGui.QFont("Courier", 12)  # Example of setting Arial font with size 12
        self.table.setFont(font)

        # Apply black background stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                color: white;
            }
            QTableWidget {
                background-color: black;
                color: white;
                gridline-color: grey;
            }
            QHeaderView::section {
                background-color: black;
                color: white;
            }
            QToolBar {
                background-color: black;
                color: white;
            }
        """)

        # Connect cellChanged signal to handle checkbox changes and priority changes
        self.table.cellChanged.connect(self.handle_cell_changed)

        # Setup timer to check for changes every 0.01 seconds
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_for_changes)
        self.timer.start(10)  # 10 milliseconds (0.01 seconds)

        # Setup timer to reorder todos every second
        self.reorder_timer = QtCore.QTimer()
        self.reorder_timer.timeout.connect(self.reorder_todos)
        self.reorder_timer.start(1000)  # 1000 milliseconds (1 second)

    def render_todos(self):
        # Sort the todos by priority in descending order initially
        self.sorted_todos = sorted(todo_data.items(), key=lambda x: x[1]['priority'], reverse=True)
        
        self.table.setRowCount(len(self.sorted_todos))
        for row, (timestamp, todo) in enumerate(self.sorted_todos):
            text = todo['text']
            priority = todo['priority']
            completed = todo['completed']

            text_item = QtWidgets.QTableWidgetItem(text)
            text_item.setFlags(text_item.flags() | QtCore.Qt.ItemIsEditable)
            text_item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            self.table.setItem(row, 0, text_item)

            # Create a QComboBox for priority
            priority_combo = QtWidgets.QComboBox()
            priority_combo.addItems([str(i) for i in range(1, 11)])  # Add priority options 1 to 10
            priority_combo.setCurrentIndex(priority - 1)  # Set current priority
            self.table.setCellWidget(row, 1, priority_combo)

            completed_item = QtWidgets.QTableWidgetItem()
            completed_item.setCheckState(QtCore.Qt.Checked if completed else QtCore.Qt.Unchecked)
            completed_item.setData(QtCore.Qt.CheckStateRole, QtCore.Qt.Checked if completed else QtCore.Qt.Unchecked)
            self.table.setItem(row, 2, completed_item)

            # Apply strikeout font if completed
            font = QtGui.QFont()
            font.setStrikeOut(completed)
            text_item.setFont(font)

            # Set text color based on priority
            color = priority_colors.get(priority, QtGui.QColor(0, 0, 0))
            text_item.setForeground(QtGui.QBrush(color))

    def handle_cell_changed(self, row, column):
        if column == 2:  # Check if the column is 'Completed'
            item = self.table.item(row, column)
            if item is not None:
                checked = item.checkState() == QtCore.Qt.Checked
                timestamp = list(todo_data.keys())[row]
                todo_data[timestamp]['completed'] = checked

                # Apply strikeout font based on completed status
                font = self.table.item(row, 0).font()
                font.setStrikeOut(checked)
                self.table.item(row, 0).setFont(font)

                # Update JSON file immediately
                update_json()

                # No need to render_todos() here to avoid recursion

    def check_for_changes(self):
        # Check for changes in text and priority columns
        for row in range(self.table.rowCount()):
            text_item = self.table.item(row, 0)
            priority_widget = self.table.cellWidget(row, 1)

            if text_item is not None and priority_widget is not None:
                timestamp = list(todo_data.keys())[row]

                # Check if text has changed
                if text_item.text() != todo_data[timestamp]['text']:
                    todo_data[timestamp]['text'] = text_item.text()
                    update_json()

                # Check if priority has changed
                current_priority = priority_widget.currentIndex() + 1
                if todo_data[timestamp]['priority'] != current_priority:
                    todo_data[timestamp]['priority'] = current_priority
                    update_json()

                    # Update text item color based on new priority
                    color = priority_colors.get(current_priority, QtGui.QColor(0, 0, 0))
                    text_item.setForeground(QtGui.QBrush(color))

    def reorder_todos(self):
        # Sort todos by priority in descending order
        self.sorted_todos = sorted(todo_data.items(), key=lambda x: x[1]['priority'], reverse=True)

        # Update table rows based on sorted todos
        self.table.setRowCount(len(self.sorted_todos))
        for row, (timestamp, todo) in enumerate(self.sorted_todos):
            text = todo['text']
            priority = todo['priority']
            completed = todo['completed']

            text_item = self.table.item(row, 0)
            text_item.setText(text)

            priority_widget = self.table.cellWidget(row, 1)
            priority_widget.setCurrentIndex(priority - 1)

            completed_item = self.table.item(row, 2)
            completed_item.setCheckState(QtCore.Qt.Checked if completed else QtCore.Qt.Unchecked)

            # Apply strikeout font if completed
            font = QtGui.QFont()
            font.setStrikeOut(completed)
            text_item.setFont(font)

            # Set text color based on priority
            color = priority_colors.get(priority, QtGui.QColor(0, 0, 0))
            text_item.setForeground(QtGui.QBrush(color))

    def create_todo(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Todo", "Enter todo text:")
        if not ok or not text:
            return

        priority, ok = QtWidgets.QInputDialog.getInt(self, "Create Todo", "Enter priority (1-10):", 1, 1, 10)
        if not ok:
            return

        timestamp = str(int(QtCore.QDateTime.currentMSecsSinceEpoch() / 1000))
        todo_data[timestamp] = {
            "text": text,
            "priority": priority,
            "completed": False
        }

        # Update JSON file immediately
        update_json()

        # Update rendering immediately after change
        self.render_todos()

    def clear_completed_todos(self):
        global todo_data
        todo_data = {timestamp: todo for timestamp, todo in todo_data.items() if not todo['completed']}
        update_json()
        self.render_todos()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    todo_list = TodoList()
    todo_list.show()
    app.exec_()