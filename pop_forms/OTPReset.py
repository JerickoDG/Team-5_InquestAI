# Form implementation generated from reading ui file 'c:\Users\ryanj\OneDrive\Desktop\PD2gui\pop_forms\OTPReset.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


import os
from PyQt6 import QtCore, QtGui, QtWidgets

MAIN_PATH = os.getcwd()
IMAGES_PATH = os.path.join(MAIN_PATH, 'image')


class Ui_OTPResetWindow(object):
    def setupUi(self, OTPResetWindow):
        OTPResetWindow.setObjectName("OTPResetWindow")
        OTPResetWindow.resize(480, 600)
        OTPResetWindow.setMinimumSize(QtCore.QSize(480, 600))
        OTPResetWindow.setMaximumSize(QtCore.QSize(480, 600))
        self.centralwidget = QtWidgets.QWidget(parent=OTPResetWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setGeometry(QtCore.QRect(160, 60, 151, 151))
        self.label.setPixmap(QtGui.QPixmap(os.path.join(IMAGES_PATH, "check.png")))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.verificationtxt = QtWidgets.QLabel(parent=self.centralwidget)
        self.verificationtxt.setGeometry(QtCore.QRect(150, 210, 171, 51))
        self.verificationtxt.setStyleSheet("font: 700 21pt \"Tahoma\";")
        self.verificationtxt.setObjectName("verificationtxt")
        self.instrtxt_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.instrtxt_2.setGeometry(QtCore.QRect(70, 260, 361, 51))
        self.instrtxt_2.setStyleSheet("font: 13pt \"Tahoma\";")
        self.instrtxt_2.setObjectName("instrtxt_2")
        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(0, 0, 481, 601))
        self.label_2.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.confirmotpreset = QtWidgets.QPushButton(parent=self.centralwidget)
        self.confirmotpreset.setGeometry(QtCore.QRect(60, 410, 171, 51))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confirmotpreset.sizePolicy().hasHeightForWidth())
        self.confirmotpreset.setSizePolicy(sizePolicy)
        self.confirmotpreset.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.confirmotpreset.setAutoFillBackground(False)
        self.confirmotpreset.setStyleSheet("#confirmotpreset {\n"
"background-color: rgb(85, 183, 221);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"color: white;\n"
"}\n"
"\n"
"#confirmotpreset:Hover {\n"
"background-color: rgb(16, 170, 215);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"color: white;\n"
"}\n"
"\n"
"#confirmotpreset:Pressed {\n"
"background-color: rgb(16, 170, 163);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"color: white;\n"
"}")
        self.confirmotpreset.setChecked(False)
        self.confirmotpreset.setAutoDefault(True)
        self.confirmotpreset.setObjectName("confirmotpreset")
        self.otpenterreset = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.otpenterreset.setGeometry(QtCore.QRect(50, 320, 381, 51))
        self.otpenterreset.setAutoFillBackground(False)
        self.otpenterreset.setStyleSheet("font: 12pt \"Tahoma\";\n"
"background-color: rgb(227, 227, 227);\n"
"border: 0.5px solid black;\n"
"border-radius: 10px;\n"
"padding: 5px;")
        self.otpenterreset.setMaxLength(6)
        self.otpenterreset.setFrame(True)
        self.otpenterreset.setEchoMode(QtWidgets.QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.otpenterreset.setPlaceholderText("One Time Password")
        self.otpenterreset.setObjectName("otpenterreset")
        self.cancelreset = QtWidgets.QPushButton(parent=self.centralwidget)
        self.cancelreset.setGeometry(QtCore.QRect(260, 410, 171, 51))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cancelreset.sizePolicy().hasHeightForWidth())
        self.cancelreset.setSizePolicy(sizePolicy)
        self.cancelreset.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.cancelreset.setAutoFillBackground(False)
        self.cancelreset.setStyleSheet("#cancelreset {\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"border: 1px solid gray;\n"
"color: black\n"
"}\n"
"\n"
"#cancelreset:Hover {\n"
"background-color: gray;\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"border: 1px solid gray;\n"
"color: white;\n"
"}\n"
"\n"
"#cancelreset:Pressed {\n"
"background-color: rgb(143, 143, 143);\n"
"font: 700 14pt \"Tahoma\";\n"
"border-radius: 10px;\n"
"border: 1px solid gray;\n"
"color: white;\n"
"}")
        self.cancelreset.setChecked(False)
        self.cancelreset.setAutoDefault(True)
        self.cancelreset.setObjectName("cancelreset")
        self.label_2.raise_()
        self.label.raise_()
        self.verificationtxt.raise_()
        self.instrtxt_2.raise_()
        self.confirmotpreset.raise_()
        self.otpenterreset.raise_()
        self.cancelreset.raise_()
        OTPResetWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(OTPResetWindow)
        QtCore.QMetaObject.connectSlotsByName(OTPResetWindow)

    def retranslateUi(self, OTPResetWindow):
        _translate = QtCore.QCoreApplication.translate
        OTPResetWindow.setWindowTitle(_translate("OTPResetWindow", "Reset Password"))
        self.verificationtxt.setText(_translate("OTPResetWindow", " Verification"))
        self.instrtxt_2.setText(_translate("OTPResetWindow", "Check your email for your One Time Password"))
        self.confirmotpreset.setText(_translate("OTPResetWindow", "Confirm"))
        self.cancelreset.setText(_translate("OTPResetWindow", "Cancel"))
