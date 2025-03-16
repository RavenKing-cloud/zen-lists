import os
import json
from PyQt5 import QtWidgets, QtGui, QtCore

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