import os
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from src.title_bar import CustomTitleBar

# Define colors for priority levels
priority_colors = {
    10: QtGui.QColor(230, 0, 0),       # red
    9: QtGui.QColor(255, 75, 0),        # red-orange
    8: QtGui.QColor(255, 150, 50),      # orange
    7: QtGui.QColor(255, 200, 0),       # yellow-orange
    6: QtGui.QColor(255, 255, 0),       # yellow
    5: QtGui.QColor(200, 255, 0),       # light green
    4: QtGui.QColor(125, 255, 0),       # grey-blue
    3: QtGui.QColor(60, 240, 0),        # blue-white
    2: QtGui.QColor(0, 220, 20),        # bright blue
    1: QtGui.QColor(0, 200, 75)         # green
}

###############################################################################
# ListTab: Each tab (or “list”) is a self-contained widget with its own JSON.
###############################################################################
class ListTab(QtWidgets.QWidget):
    def __init__(self, json_file_path, parent=None):
        super().__init__(parent)
        self.json_file_path = json_file_path
        self.list_data = self.load_json()
        self.setup_ui()

        # Monitor cell changes and periodic updates.
        self.table.cellChanged.connect(self.handle_cell_changed)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.check_for_changes)
        self.timer.start(10)  # every 10 ms

        self.reorder_timer = QtCore.QTimer(self)
        self.reorder_timer.timeout.connect(self.reorder_entries)
        self.reorder_timer.start(1000)  # every 1 second

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        # Internal toolbar: New Entry and Clear Completed.
        self.internal_toolbar = QtWidgets.QToolBar("List Toolbar", self)
        self.internal_toolbar.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.internal_toolbar)

        new_entry_action = QtWidgets.QAction("New Entry", self)
        new_entry_action.triggered.connect(self.create_entry)
        self.internal_toolbar.addAction(new_entry_action)

        clear_completed_action = QtWidgets.QAction("Clear Completed", self)
        clear_completed_action.triggered.connect(self.clear_completed_entries)
        self.internal_toolbar.addAction(clear_completed_action)

        # Table for list entries.
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Text", "Priority", "Completed"])
        layout.addWidget(self.table)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

        font = QtGui.QFont("Courier", 12)
        self.table.setFont(font)
        self.setStyleSheet("""
            QWidget { background-color: black; color: white; }
            QTableWidget { background-color: black; color: white; gridline-color: grey; }
            QHeaderView::section { background-color: black; color: white; }
            QToolBar { background-color: black; color: white; }
        """)
        self.render_entries()

    def load_json(self):
        # If the file doesn’t exist or is empty, create a default entry.
        if not os.path.exists(self.json_file_path):
            with open(self.json_file_path, 'w') as f:
                default_list = {
                    "example_entry": {
                        "text": "Example Entry",
                        "priority": 5,
                        "completed": False
                    }
                }
                json.dump(default_list, f, indent=4)
                return default_list
        with open(self.json_file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        if not data:
            default_list = {
                "example_entry": {
                    "text": "Example Entry",
                    "priority": 5,
                    "completed": False
                }
            }
            data.update(default_list)
            with open(self.json_file_path, 'w') as f:
                json.dump(data, f, indent=4)
        return data

    def update_json(self):
        with open(self.json_file_path, 'w') as f:
            json.dump(self.list_data, f, indent=4)

    def render_entries(self):
        sorted_entries = sorted(self.list_data.items(), key=lambda x: x[1]['priority'], reverse=True)
        self.table.setRowCount(len(sorted_entries))
        for row, (timestamp, entry) in enumerate(sorted_entries):
            text = entry['text']
            priority = entry['priority']
            completed = entry['completed']

            text_item = QtWidgets.QTableWidgetItem(text)
            text_item.setFlags(text_item.flags() | QtCore.Qt.ItemIsEditable)
            text_item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            self.table.setItem(row, 0, text_item)

            priority_combo = QtWidgets.QComboBox()
            priority_combo.addItems([str(i) for i in range(1, 11)])
            priority_combo.setCurrentIndex(priority - 1)
            self.table.setCellWidget(row, 1, priority_combo)

            completed_item = QtWidgets.QTableWidgetItem()
            completed_item.setCheckState(QtCore.Qt.Checked if completed else QtCore.Qt.Unchecked)
            completed_item.setData(QtCore.Qt.CheckStateRole, QtCore.Qt.Checked if completed else QtCore.Qt.Unchecked)
            self.table.setItem(row, 2, completed_item)

            font = QtGui.QFont()
            font.setStrikeOut(completed)
            text_item.setFont(font)

            color = priority_colors.get(priority, QtGui.QColor(0, 0, 0))
            text_item.setForeground(QtGui.QBrush(color))

    def handle_cell_changed(self, row, column):
        if column == 2:
            item = self.table.item(row, column)
            if item is not None:
                checked = item.checkState() == QtCore.Qt.Checked
                sorted_keys = sorted(self.list_data.keys(), key=lambda k: self.list_data[k]['priority'], reverse=True)
                if row < len(sorted_keys):
                    timestamp = sorted_keys[row]
                    self.list_data[timestamp]['completed'] = checked
                    font = self.table.item(row, 0).font()
                    font.setStrikeOut(checked)
                    self.table.item(row, 0).setFont(font)
                    self.update_json()

    def check_for_changes(self):
        for row in range(self.table.rowCount()):
            text_item = self.table.item(row, 0)
            priority_widget = self.table.cellWidget(row, 1)
            if text_item is not None and priority_widget is not None:
                sorted_keys = sorted(self.list_data.keys(), key=lambda k: self.list_data[k]['priority'], reverse=True)
                if row < len(sorted_keys):
                    timestamp = sorted_keys[row]
                    if text_item.text() != self.list_data[timestamp]['text']:
                        self.list_data[timestamp]['text'] = text_item.text()
                        self.update_json()
                    current_priority = priority_widget.currentIndex() + 1
                    if self.list_data[timestamp]['priority'] != current_priority:
                        self.list_data[timestamp]['priority'] = current_priority
                        self.update_json()
                        color = priority_colors.get(current_priority, QtGui.QColor(0, 0, 0))
                        text_item.setForeground(QtGui.QBrush(color))

    def reorder_entries(self):
        sorted_entries = sorted(self.list_data.items(), key=lambda x: x[1]['priority'], reverse=True)
        self.table.setRowCount(len(sorted_entries))
        for row, (timestamp, entry) in enumerate(sorted_entries):
            text = entry['text']
            priority = entry['priority']
            completed = entry['completed']
            text_item = self.table.item(row, 0)
            if text_item is not None:
                text_item.setText(text)
            else:
                text_item = QtWidgets.QTableWidgetItem(text)
                self.table.setItem(row, 0, text_item)
            priority_widget = self.table.cellWidget(row, 1)
            if priority_widget is not None:
                priority_widget.setCurrentIndex(priority - 1)
            else:
                priority_combo = QtWidgets.QComboBox()
                priority_combo.addItems([str(i) for i in range(1, 11)])
                priority_combo.setCurrentIndex(priority - 1)
                self.table.setCellWidget(row, 1, priority_combo)
            completed_item = self.table.item(row, 2)
            if completed_item is not None:
                completed_item.setCheckState(QtCore.Qt.Checked if completed else QtCore.Qt.Unchecked)
            else:
                completed_item = QtWidgets.QTableWidgetItem()
                completed_item.setCheckState(QtCore.Qt.Checked if completed else QtCore.Qt.Unchecked)
                self.table.setItem(row, 2, completed_item)
            font = QtGui.QFont()
            font.setStrikeOut(completed)
            text_item.setFont(font)
            color = priority_colors.get(priority, QtGui.QColor(0, 0, 0))
            text_item.setForeground(QtGui.QBrush(color))

    def create_entry(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "New Entry", "Enter entry text:")
        if not ok or not text:
            return
        priority, ok = QtWidgets.QInputDialog.getInt(self, "New Entry", "Enter priority (1-10):", 1, 1, 10)
        if not ok:
            return
        timestamp = str(int(QtCore.QDateTime.currentMSecsSinceEpoch() / 1000))
        self.list_data[timestamp] = {
            "text": text,
            "priority": priority,
            "completed": False
        }
        self.update_json()
        self.render_entries()

    def clear_completed_entries(self):
        self.list_data = {ts: entry for ts, entry in self.list_data.items() if not entry['completed']}
        self.update_json()
        self.render_entries()

    def save_list(self):
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        new_file, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save List", base_dir, "JSON Files (*.json)")
        if new_file:
            with open(new_file, 'w') as f:
                json.dump(self.list_data, f, indent=4)
            self.json_file_path = new_file
            return new_file
        return None

###############################################################################
# MainWindow: Manages the overall interface, tabs, caching, and drop-down menus.
###############################################################################
class MainWindow(QtWidgets.QMainWindow):
    MAX_VISIBLE_TABS = 5

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-List Application")
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(1000, 700)

        # Containers for loaded lists.
        self.visible_tabs = []   # List of tuples: (file_path, ListTab)
        self.cached_tabs = []    # Tabs not currently displayed

        # Central widget and layout.
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Custom title bar.
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setStyleSheet("background-color: black; color: white;")
        self.main_layout.addWidget(self.title_bar)
        self.title_bar.installEventFilter(self)
        self.drag_position = None

        # Top toolbar: Left side dropdown for list options and right side dropdown for hidden lists.
        self.top_toolbar = QtWidgets.QToolBar("Main Toolbar")
        self.top_toolbar.setStyleSheet("background-color: black; color: white;")
        self.main_layout.addWidget(self.top_toolbar)

        # Left: Sleek QPushButton with dropdown for list options.
        self.options_button = QtWidgets.QPushButton("List Options")
        self.options_button.setStyleSheet("QPushButton { background-color: black; color: white; border: none; }")
        options_menu = QtWidgets.QMenu()
        options_menu.addAction("New List", self.new_list)
        options_menu.addAction("Open List", self.open_list)
        options_menu.addAction("Save List", self.save_list_current)
        options_menu.addAction("Delete List", self.delete_list)
        self.options_button.setMenu(options_menu)
        self.top_toolbar.addWidget(self.options_button)

        # Add spacer to push next widget to right.
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.top_toolbar.addWidget(spacer)

        # Right: Dropdown for hidden (cached) lists.
        self.hidden_button = QtWidgets.QPushButton("Hidden Lists")
        self.hidden_button.setStyleSheet("QPushButton { background-color: black; color: white; border: none; }")
        self.hidden_menu = QtWidgets.QMenu()
        self.hidden_button.setMenu(self.hidden_menu)
        self.top_toolbar.addWidget(self.hidden_button)

        # QTabWidget for visible lists.
        self.tab_widget = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        self.tab_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.tab_context_menu)

        # Load all lists from the data folder.
        self.load_all_lists()
        self.update_hidden_lists_menu()

        # Apply full dark theme.
        self.setStyleSheet("""
            QWidget { background-color: black; color: white; }
            QTableWidget { background-color: black; color: white; gridline-color: grey; }
            QHeaderView::section { background-color: black; color: white; }
            QToolBar { background-color: black; color: white; }
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: black; color: white; padding: 5px; }
            QTabBar::tab:selected { background: grey; }
        """)

    def eventFilter(self, source, event):
        if source == self.title_bar:
            if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return True
            elif event.type() == QtCore.QEvent.MouseMove and event.buttons() == QtCore.Qt.LeftButton and self.drag_position:
                self.move(event.globalPos() - self.drag_position)
                event.accept()
                return True
        return super().eventFilter(source, event)

    def load_all_lists(self):
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        files = sorted([f for f in os.listdir(base_dir) if f.endswith(".json")])
        # Clear any existing tabs.
        self.visible_tabs = []
        self.cached_tabs = []
        self.tab_widget.clear()
        for f in files:
            file_path = os.path.join(base_dir, f)
            # Create ListTab.
            tab = ListTab(file_path)
            # Use the file name (without extension) as the list name.
            tab_name = os.path.splitext(f)[0]
            if len(self.visible_tabs) < self.MAX_VISIBLE_TABS:
                self.visible_tabs.append((file_path, tab))
                self.tab_widget.addTab(tab, tab_name)
            else:
                self.cached_tabs.append((file_path, tab))

    def update_hidden_lists_menu(self):
        self.hidden_menu.clear()
        for file_path, tab in self.cached_tabs:
            name = os.path.splitext(os.path.basename(file_path))[0]
            action = self.hidden_menu.addAction(name)
            action.triggered.connect(lambda checked, fp=file_path, t=tab: self.bring_hidden_to_visible(fp, t))
        # Also update Delete List menu (if needed in options).

    def bring_hidden_to_visible(self, file_path, tab):
        # Remove from cached.
        self.cached_tabs = [item for item in self.cached_tabs if item[0] != file_path]
        # Insert at index 0 in QTabWidget.
        self.tab_widget.insertTab(0, tab, os.path.splitext(os.path.basename(file_path))[0])
        self.visible_tabs.insert(0, (file_path, tab))
        # If visible_tabs exceeds limit, move last one to cached.
        if len(self.visible_tabs) > self.MAX_VISIBLE_TABS:
            removed_file, removed_tab = self.visible_tabs.pop()
            index = self.tab_widget.indexOf(removed_tab)
            if index != -1:
                self.tab_widget.removeTab(index)
            self.cached_tabs.insert(0, (removed_file, removed_tab))
        self.update_hidden_lists_menu()

    def new_list(self):
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "New List", base_dir, "JSON Files (*.json)")
        if file_name:
            if not os.path.exists(file_name):
                default_data = {
                    "example_entry": {
                        "text": "Example Entry",
                        "priority": 5,
                        "completed": False
                    }
                }
                with open(file_name, 'w') as f:
                    json.dump(default_data, f, indent=4)
            tab = ListTab(file_name)
            tab_name = os.path.splitext(os.path.basename(file_name))[0]
            # Insert new list as the first (leftmost) tab.
            self.tab_widget.insertTab(0, tab, tab_name)
            self.visible_tabs.insert(0, (file_name, tab))
            if len(self.visible_tabs) > self.MAX_VISIBLE_TABS:
                removed_file, removed_tab = self.visible_tabs.pop()
                index = self.tab_widget.indexOf(removed_tab)
                if index != -1:
                    self.tab_widget.removeTab(index)
                self.cached_tabs.insert(0, (removed_file, removed_tab))
            self.update_hidden_lists_menu()

    def open_list(self):
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open List", base_dir, "JSON Files (*.json)")
        if file_name:
            # Check if already loaded.
            for fp, tab in self.visible_tabs + self.cached_tabs:
                if os.path.abspath(fp) == os.path.abspath(file_name):
                    # Bring to visible.
                    self.bring_hidden_to_visible(fp, tab)
                    return
            tab = ListTab(file_name)
            tab_name = os.path.splitext(os.path.basename(file_name))[0]
            self.tab_widget.insertTab(0, tab, tab_name)
            self.visible_tabs.insert(0, (file_name, tab))
            if len(self.visible_tabs) > self.MAX_VISIBLE_TABS:
                removed_file, removed_tab = self.visible_tabs.pop()
                index = self.tab_widget.indexOf(removed_tab)
                if index != -1:
                    self.tab_widget.removeTab(index)
                self.cached_tabs.insert(0, (removed_file, removed_tab))
            self.update_hidden_lists_menu()

    def save_list_current(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab is not None and hasattr(current_tab, "save_list"):
            new_file = current_tab.save_list()
            if new_file:
                index = self.tab_widget.indexOf(current_tab)
                self.tab_widget.setTabText(index, os.path.splitext(os.path.basename(new_file))[0])
                # Update visible_tabs.
                for i, (fp, tab) in enumerate(self.visible_tabs):
                    if tab == current_tab:
                        self.visible_tabs[i] = (new_file, tab)
                        break

    def delete_list(self):
        # Show a menu listing all .json files in the data folder.
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        files = sorted([f for f in os.listdir(base_dir) if f.endswith(".json")])
        menu = QtWidgets.QMenu()
        for f in files:
            file_path = os.path.join(base_dir, f)
            action = menu.addAction(os.path.splitext(f)[0])
            action.triggered.connect(lambda checked, fp=file_path: self.delete_list_file(fp))
        menu.exec_(QtGui.QCursor.pos())

    def delete_list_file(self, file_path):
        reply = QtWidgets.QMessageBox.question(self, 'Confirm Delete',
                                               f"Are you sure you want to delete '{os.path.basename(file_path)}'?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            # Remove tab if loaded.
            for lst in (self.visible_tabs, self.cached_tabs):
                for item in lst:
                    fp, tab = item
                    if os.path.abspath(fp) == os.path.abspath(file_path):
                        if tab in [t for _, t in self.visible_tabs]:
                            index = self.tab_widget.indexOf(tab)
                            if index != -1:
                                self.tab_widget.removeTab(index)
                            self.visible_tabs = [i for i in self.visible_tabs if i[0] != file_path]
                        else:
                            self.cached_tabs = [i for i in self.cached_tabs if i[0] != file_path]
                        break
            try:
                os.remove(file_path)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not delete file:\n{e}")
            self.update_hidden_lists_menu()

    def tab_context_menu(self, pos):
        tab_bar = self.tab_widget.tabBar()
        index = tab_bar.tabAt(pos)
        if index != -1:
            menu = QtWidgets.QMenu()
            close_action = menu.addAction("Close Tab")
            action = menu.exec_(tab_bar.mapToGlobal(pos))
            if action == close_action:
                # Remove the tab from visible_tabs.
                widget = self.tab_widget.widget(index)
                file_path = None
                for fp, tab in self.visible_tabs:
                    if tab == widget:
                        file_path = fp
                        break
                self.tab_widget.removeTab(index)
                self.visible_tabs = [i for i in self.visible_tabs if i[0] != file_path]
                # If any cached tabs exist, fill the gap.
                if self.cached_tabs:
                    cached_fp, cached_tab = self.cached_tabs.pop(0)
                    self.tab_widget.insertTab(index, cached_tab, os.path.splitext(os.path.basename(cached_fp))[0])
                    self.visible_tabs.insert(index, (cached_fp, cached_tab))
                self.update_hidden_lists_menu()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())