# Form implementation generated from reading ui file 'c:\Users\ryanj\OneDrive\Desktop\PD2gui\pop_forms\PassReset.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.

import os
from PyQt6 import QtCore, QtGui, QtWidgets

MAIN_PATH = os.getcwd()
IMAGES_PATH = os.path.join(MAIN_PATH, 'image')


class Ui_ResetPassWindow(object):
    def setupUi(self, ResetPassWindow):
        ResetPassWindow.setObjectName("ResetPassWindow")
        ResetPassWindow.resize(480, 600)
        ResetPassWindow.setMinimumSize(QtCore.QSize(480, 600))
        ResetPassWindow.setMaximumSize(QtCore.QSize(480, 600))
        self.centralwidget = QtWidgets.QWidget(parent=ResetPassWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setGeometry(QtCore.QRect(160, 60, 151, 151))
        self.label.setPixmap(QtGui.QPixmap(os.path.join(IMAGES_PATH, "check.png")))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.verificationtxt = QtWidgets.QLabel(parent=self.centralwidget)
        self.verificationtxt.setGeometry(QtCore.QRect(170, 210, 121, 51))
        self.verificationtxt.setStyleSheet("font: 700 21pt \"Tahoma\";")
        self.verificationtxt.setObjectName("verificationtxt")
        self.instrtxt_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.instrtxt_2.setGeometry(QtCore.QRect(150, 260, 181, 51))
        self.instrtxt_2.setStyleSheet("font: 13pt \"Tahoma\";")
        self.instrtxt_2.setObjectName("instrtxt_2")
        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(0, 0, 481, 601))
        self.label_2.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.newpass = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.newpass.setGeometry(QtCore.QRect(50, 320, 381, 51))
        self.newpass.setAutoFillBackground(False)
        self.newpass.setStyleSheet("font: 12pt \"Tahoma\";\n"
"background-color: rgb(227, 227, 227);\n"
"border: 0.5px solid black;\n"
"border-radius: 10px;\n"
"padding: 5px;")
        self.newpass.setMaxLength(30)
        self.newpass.setFrame(True)
        self.newpass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.newpass.setPlaceholderText("New Password")
        self.newpass.setObjectName("newpass")
        self.update_newpass = QtWidgets.QPushButton(parent=self.centralwidget)
        self.update_newpass.setGeometry(QtCore.QRect(60, 480, 171, 51))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.update_newpass.sizePolicy().hasHeightForWidth())
        self.update_newpass.setSizePolicy(sizePolicy)
        self.update_newpass.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.update_newpass.setAutoFillBackground(False)
        self.update_newpass.setStyleSheet("#update_newpass {\n"
"background-color: rgb(85, 183, 221);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"color: white;\n"
"}\n"
"\n"
"#update_newpass:Hover {\n"
"background-color: rgb(16, 170, 215);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"color: white;\n"
"}\n"
"\n"
"#update_newpass:Pressed {\n"
"background-color: rgb(16, 170, 163);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"color: white;\n"
"}")
        self.update_newpass.setChecked(False)
        self.update_newpass.setAutoDefault(True)
        self.update_newpass.setObjectName("update_newpass")
        self.confirm_newpass = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.confirm_newpass.setGeometry(QtCore.QRect(50, 400, 381, 51))
        self.confirm_newpass.setAutoFillBackground(False)
        self.confirm_newpass.setStyleSheet("font: 12pt \"Tahoma\";\n"
"background-color: rgb(227, 227, 227);\n"
"border: 0.5px solid black;\n"
"border-radius: 10px;\n"
"padding: 5px;")
        self.confirm_newpass.setMaxLength(30)
        self.confirm_newpass.setFrame(True)
        self.confirm_newpass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.confirm_newpass.setPlaceholderText("Confirm Password")
        self.confirm_newpass.setObjectName("confirm_newpass")
        self.confpassreveal = QtWidgets.QLabel(parent=self.centralwidget)
        self.confpassreveal.setGeometry(QtCore.QRect(390, 410, 31, 31))
        self.confpassreveal.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.confpassreveal.setText("")
        self.confpassreveal.setPixmap(QtGui.QPixmap(os.path.join(IMAGES_PATH,'invisible.png')))
        self.confpassreveal.setScaledContents(True)
        self.confpassreveal.setObjectName("confpassreveal")
        self.newpassreveal = QtWidgets.QLabel(parent=self.centralwidget)
        self.newpassreveal.setGeometry(QtCore.QRect(390, 330, 31, 31))
        self.newpassreveal.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.newpassreveal.setText("")
        self.newpassreveal.setPixmap(QtGui.QPixmap(os.path.join(IMAGES_PATH,'invisible.png')))
        self.newpassreveal.setScaledContents(True)
        self.newpassreveal.setObjectName("newpassreveal")
        self.emailcontainer = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.emailcontainer.setGeometry(QtCore.QRect(180, 130, 113, 22))
        self.emailcontainer.setStyleSheet("border-color: rgb(255, 255, 255);")
        self.emailcontainer.setObjectName("emailcontainer")
        self.passcancelreset = QtWidgets.QPushButton(parent=self.centralwidget)
        self.passcancelreset.setGeometry(QtCore.QRect(250, 480, 171, 51))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.passcancelreset.sizePolicy().hasHeightForWidth())
        self.passcancelreset.setSizePolicy(sizePolicy)
        self.passcancelreset.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.passcancelreset.setAutoFillBackground(False)
        self.passcancelreset.setStyleSheet("#passcancelreset {\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"border: 1px solid gray;\n"
"color: black\n"
"}\n"
"#passcancelreset:Hover {\n"
"background-color: gray;\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"border: 1px solid gray;\n"
"color: white;\n"
"}\n"
"#passcancelreset :Pressed {\n"
"background-color: rgb(143, 143, 143);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"border: 1px solid gray;\n"
"color: white;\n"
"}")
        self.passcancelreset.setChecked(False)
        self.passcancelreset.setAutoDefault(True)
        self.passcancelreset.setObjectName("passcancelreset")
        self.label_2.raise_()
        self.verificationtxt.raise_()
        self.instrtxt_2.raise_()
        self.newpass.raise_()
        self.update_newpass.raise_()
        self.confirm_newpass.raise_()
        self.confpassreveal.raise_()
        self.newpassreveal.raise_()
        self.emailcontainer.raise_()
        self.label.raise_()
        self.passcancelreset.raise_()
        ResetPassWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(ResetPassWindow)
        QtCore.QMetaObject.connectSlotsByName(ResetPassWindow)

    def retranslateUi(self, ResetPassWindow):
        _translate = QtCore.QCoreApplication.translate
        ResetPassWindow.setWindowTitle(_translate("ResetPassWindow", "Reset Password"))
        self.verificationtxt.setText(_translate("ResetPassWindow", " Verified"))
        self.instrtxt_2.setText(_translate("ResetPassWindow", "Set Your New Password"))
        self.update_newpass.setText(_translate("ResetPassWindow", "Confirm"))
        self.passcancelreset.setText(_translate("ResetPassWindow", "Cancel"))
