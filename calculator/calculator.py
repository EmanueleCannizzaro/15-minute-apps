# -*- coding: utf-8 -*-

# This Python file uses the following encoding: utf-8


# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.10
#
# WARNING! All changes made in this file will be lost!


from datetime import datetime
import json
import os
import sys
import argparse
import requests
from urllib.parse import urlencode

from PySide2.QtCore import (QCoreApplication, QMetaObject, QRect, QSize)
from PySide2.QtGui import QFont
from PySide2.QtWidgets import (QAction, QApplication, QGridLayout, QLCDNumber, QMenu, QMenuBar, QSizePolicy, QMainWindow, QPushButton, QStatusBar, QVBoxLayout, QWidget)

import operator

#from MainWindow import Ui_MainWindow

# Calculator state.
READY = 0
INPUT = 1


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # Setup numbers.
        for n in range(0, 10):
            getattr(self, 'pushButton_n%s' % n).pressed.connect(lambda v=n: self.input_number(v))

        # Setup operations.
        self.pushButton_add.pressed.connect(lambda: self.operation(operator.add))
        self.pushButton_sub.pressed.connect(lambda: self.operation(operator.sub))
        self.pushButton_mul.pressed.connect(lambda: self.operation(operator.mul))
        self.pushButton_div.pressed.connect(lambda: self.operation(operator.truediv))  # operator.div for Python2.7

        self.pushButton_pc.pressed.connect(self.operation_pc)
        self.pushButton_eq.pressed.connect(self.equals)

        # Setup actions
        self.actionReset.triggered.connect(self.reset)
        self.pushButton_ac.pressed.connect(self.reset)

        self.actionExit.triggered.connect(self.close)

        self.pushButton_m.pressed.connect(self.memory_store)
        self.pushButton_mr.pressed.connect(self.memory_recall)

        self.memory = 0
        self.reset()

        self.show()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(484, 433)
        self.centralWidget = QWidget(MainWindow)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralWidget.sizePolicy().hasHeightForWidth())
        self.centralWidget.setSizePolicy(sizePolicy)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralWidget)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lcdNumber = QLCDNumber(self.centralWidget)
        self.lcdNumber.setDigitCount(10)
        self.lcdNumber.setObjectName("lcdNumber")
        self.verticalLayout.addWidget(self.lcdNumber)
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton_n4 = QPushButton(self.centralWidget)
        self.pushButton_n4.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n4.setFont(font)
        self.pushButton_n4.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n4.setObjectName("pushButton_n4")
        self.gridLayout.addWidget(self.pushButton_n4, 3, 0, 1, 1)
        self.pushButton_n1 = QPushButton(self.centralWidget)
        self.pushButton_n1.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n1.setFont(font)
        self.pushButton_n1.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n1.setObjectName("pushButton_n1")
        self.gridLayout.addWidget(self.pushButton_n1, 4, 0, 1, 1)
        self.pushButton_n8 = QPushButton(self.centralWidget)
        self.pushButton_n8.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n8.setFont(font)
        self.pushButton_n8.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n8.setObjectName("pushButton_n8")
        self.gridLayout.addWidget(self.pushButton_n8, 2, 1, 1, 1)
        self.pushButton_mul = QPushButton(self.centralWidget)
        self.pushButton_mul.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_mul.setFont(font)
        self.pushButton_mul.setObjectName("pushButton_mul")
        self.gridLayout.addWidget(self.pushButton_mul, 2, 3, 1, 1)
        self.pushButton_n7 = QPushButton(self.centralWidget)
        self.pushButton_n7.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n7.setFont(font)
        self.pushButton_n7.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n7.setObjectName("pushButton_n7")
        self.gridLayout.addWidget(self.pushButton_n7, 2, 0, 1, 1)
        self.pushButton_n6 = QPushButton(self.centralWidget)
        self.pushButton_n6.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n6.setFont(font)
        self.pushButton_n6.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n6.setObjectName("pushButton_n6")
        self.gridLayout.addWidget(self.pushButton_n6, 3, 2, 1, 1)
        self.pushButton_n5 = QPushButton(self.centralWidget)
        self.pushButton_n5.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n5.setFont(font)
        self.pushButton_n5.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n5.setObjectName("pushButton_n5")
        self.gridLayout.addWidget(self.pushButton_n5, 3, 1, 1, 1)
        self.pushButton_n0 = QPushButton(self.centralWidget)
        self.pushButton_n0.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n0.setFont(font)
        self.pushButton_n0.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n0.setObjectName("pushButton_n0")
        self.gridLayout.addWidget(self.pushButton_n0, 5, 0, 1, 1)
        self.pushButton_n2 = QPushButton(self.centralWidget)
        self.pushButton_n2.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n2.setFont(font)
        self.pushButton_n2.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n2.setObjectName("pushButton_n2")
        self.gridLayout.addWidget(self.pushButton_n2, 4, 1, 1, 1)
        self.pushButton_n9 = QPushButton(self.centralWidget)
        self.pushButton_n9.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n9.setFont(font)
        self.pushButton_n9.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n9.setObjectName("pushButton_n9")
        self.gridLayout.addWidget(self.pushButton_n9, 2, 2, 1, 1)
        self.pushButton_n3 = QPushButton(self.centralWidget)
        self.pushButton_n3.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_n3.setFont(font)
        self.pushButton_n3.setStyleSheet("QPushButton {\n"
"color: #1976D2;\n"
"}")
        self.pushButton_n3.setObjectName("pushButton_n3")
        self.gridLayout.addWidget(self.pushButton_n3, 4, 2, 1, 1)
        self.pushButton_div = QPushButton(self.centralWidget)
        self.pushButton_div.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_div.setFont(font)
        self.pushButton_div.setObjectName("pushButton_div")
        self.gridLayout.addWidget(self.pushButton_div, 1, 3, 1, 1)
        self.pushButton_sub = QPushButton(self.centralWidget)
        self.pushButton_sub.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_sub.setFont(font)
        self.pushButton_sub.setObjectName("pushButton_sub")
        self.gridLayout.addWidget(self.pushButton_sub, 3, 3, 1, 1)
        self.pushButton_add = QPushButton(self.centralWidget)
        self.pushButton_add.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_add.setFont(font)
        self.pushButton_add.setObjectName("pushButton_add")
        self.gridLayout.addWidget(self.pushButton_add, 4, 3, 1, 1)
        self.pushButton_ac = QPushButton(self.centralWidget)
        self.pushButton_ac.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_ac.setFont(font)
        self.pushButton_ac.setStyleSheet("QPushButton {\n"
"    color: #f44336;\n"
"}")
        self.pushButton_ac.setObjectName("pushButton_ac")
        self.gridLayout.addWidget(self.pushButton_ac, 1, 0, 1, 1)
        self.pushButton_mr = QPushButton(self.centralWidget)
        self.pushButton_mr.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_mr.setFont(font)
        self.pushButton_mr.setStyleSheet("QPushButton {\n"
"   color: #FFC107;\n"
"}")
        self.pushButton_mr.setObjectName("pushButton_mr")
        self.gridLayout.addWidget(self.pushButton_mr, 1, 2, 1, 1)
        self.pushButton_m = QPushButton(self.centralWidget)
        self.pushButton_m.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_m.setFont(font)
        self.pushButton_m.setStyleSheet("QPushButton {\n"
"   color: #FFC107;\n"
"}")
        self.pushButton_m.setObjectName("pushButton_m")
        self.gridLayout.addWidget(self.pushButton_m, 1, 1, 1, 1)
        self.pushButton_pc = QPushButton(self.centralWidget)
        self.pushButton_pc.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_pc.setFont(font)
        self.pushButton_pc.setObjectName("pushButton_pc")
        self.gridLayout.addWidget(self.pushButton_pc, 5, 1, 1, 1)
        self.pushButton_eq = QPushButton(self.centralWidget)
        self.pushButton_eq.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(27)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_eq.setFont(font)
        self.pushButton_eq.setStyleSheet("QPushButton {\n"
"color: #4CAF50;\n"
"}")
        self.pushButton_eq.setObjectName("pushButton_eq")
        self.gridLayout.addWidget(self.pushButton_eq, 5, 2, 1, 2)
        self.verticalLayout.addLayout(self.gridLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setGeometry(QRect(0, 0, 484, 22))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionReset = QAction(MainWindow)
        self.actionReset.setObjectName("actionReset")
        self.menuFile.addAction(self.actionReset)
        self.menuFile.addAction(self.actionExit)
        self.menuBar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Calculon"))
        self.pushButton_n4.setText(_translate("MainWindow", "4"))
        self.pushButton_n4.setShortcut(_translate("MainWindow", "4"))
        self.pushButton_n1.setText(_translate("MainWindow", "1"))
        self.pushButton_n1.setShortcut(_translate("MainWindow", "1"))
        self.pushButton_n8.setText(_translate("MainWindow", "8"))
        self.pushButton_n8.setShortcut(_translate("MainWindow", "8"))
        self.pushButton_mul.setText(_translate("MainWindow", "x"))
        self.pushButton_mul.setShortcut(_translate("MainWindow", "*"))
        self.pushButton_n7.setText(_translate("MainWindow", "7"))
        self.pushButton_n7.setShortcut(_translate("MainWindow", "7"))
        self.pushButton_n6.setText(_translate("MainWindow", "6"))
        self.pushButton_n6.setShortcut(_translate("MainWindow", "6"))
        self.pushButton_n5.setText(_translate("MainWindow", "5"))
        self.pushButton_n5.setShortcut(_translate("MainWindow", "5"))
        self.pushButton_n0.setText(_translate("MainWindow", "0"))
        self.pushButton_n0.setShortcut(_translate("MainWindow", "0"))
        self.pushButton_n2.setText(_translate("MainWindow", "2"))
        self.pushButton_n2.setShortcut(_translate("MainWindow", "2"))
        self.pushButton_n9.setText(_translate("MainWindow", "9"))
        self.pushButton_n9.setShortcut(_translate("MainWindow", "9"))
        self.pushButton_n3.setText(_translate("MainWindow", "3"))
        self.pushButton_n3.setShortcut(_translate("MainWindow", "3"))
        self.pushButton_div.setText(_translate("MainWindow", "÷"))
        self.pushButton_div.setShortcut(_translate("MainWindow", "/"))
        self.pushButton_sub.setText(_translate("MainWindow", "-"))
        self.pushButton_sub.setShortcut(_translate("MainWindow", "-"))
        self.pushButton_add.setText(_translate("MainWindow", "+"))
        self.pushButton_add.setShortcut(_translate("MainWindow", "+"))
        self.pushButton_ac.setText(_translate("MainWindow", "AC"))
        self.pushButton_ac.setShortcut(_translate("MainWindow", "Esc"))
        self.pushButton_mr.setText(_translate("MainWindow", "MR"))
        self.pushButton_mr.setShortcut(_translate("MainWindow", "R"))
        self.pushButton_m.setText(_translate("MainWindow", "M"))
        self.pushButton_m.setShortcut(_translate("MainWindow", "M"))
        self.pushButton_pc.setText(_translate("MainWindow", "%"))
        self.pushButton_pc.setShortcut(_translate("MainWindow", "%"))
        self.pushButton_eq.setText(_translate("MainWindow", "="))
        self.pushButton_eq.setShortcut(_translate("MainWindow", "Return"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionExit.setShortcut(_translate("MainWindow", "Ctrl+Q"))
        self.actionReset.setText(_translate("MainWindow", "Reset"))
        self.actionReset.setShortcut(_translate("MainWindow", "Ctrl+R"))


    def display(self):
        self.lcdNumber.display(self.stack[-1])

    def reset(self):
        self.state = READY
        self.stack = [0]
        self.last_operation = None
        self.current_op = None
        self.display()

    def memory_store(self):
        self.memory = self.lcdNumber.value()

    def memory_recall(self):
        self.state = INPUT
        self.stack[-1] = self.memory
        self.display()

    def input_number(self, v):
        if self.state == READY:
            self.state = INPUT
            self.stack[-1] = v
        else:
            self.stack[-1] = self.stack[-1] * 10 + v

        self.display()

    def operation(self, op):
        if self.current_op:  # Complete the current operation
            self.equals()

        self.stack.append(0)
        self.state = INPUT
        self.current_op = op

    def operation_pc(self):
        self.state = INPUT
        self.stack[-1] *= 0.01
        self.display()

    def equals(self):
        # Support to allow '=' to repeat previous operation
        # if no further input has been added.
        if self.state == READY and self.last_operation:
            s, self.current_op = self.last_operation
            self.stack.append(s)

        if self.current_op:
            self.last_operation = self.stack[-1], self.current_op

            try:
                self.stack = [self.current_op(*self.stack)]
            except Exception:
                self.lcdNumber.display('Err')
                self.stack = [0]
            else:
                self.current_op = None
                self.state = READY
                self.display()


if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName("Calculon")

    window = MainWindow()
    app.exec_()
