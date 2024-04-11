import sys, sqlite3, re, math, random, smtplib, threading, os, glob, pytz, json, cv2, logging, subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import timedelta, datetime
from moviepy.editor import VideoFileClip
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QDateTime
from PyQt6.QtGui import QGuiApplication, QFont
from PyQt6.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QTableWidget, QLineEdit, QFileDialog, QLabel, QProgressDialog, QHeaderView
from main_uis.login import Ui_Login
from main_uis.register import Ui_Register
from main_uis.main import Ui_MainWindow
from pop_forms.datapolicy import Ui_dataprivacy
from pop_forms.forgotpass import Ui_Reset
from pop_forms.OTPReg import Ui_OTPWindow
from pop_forms.OTPReset import Ui_OTPResetWindow
from pop_forms.PassReset import Ui_ResetPassWindow
from pop_forms.updatepass import Ui_updatesettings
from pop_forms.changepass import Ui_ChangePassWindow
from notif_ui.expired_otp import Ui_expiredotp
from notif_ui.warning_window import Ui_alert_win
from notif_ui.success_window import Ui_success_win
from notif_ui.failed_window import Ui_failed_win
from notif_ui.logout_win import Ui_logout_win
from notif_ui.warning_param import Ui_param_win
from videoplayer.videoplayer import VideoPlayer
import clothing_and_weapon_detection as cwd
import pytz
import datetime
from datetime import datetime
from win32com.propsys import propsys, pscon
from functools import partial
import clothing_color_identification

MAIN_PATH = os.getcwd()
TEMP_OUTPUT_PATH = os.path.join(MAIN_PATH, 'temp_output')
USER_APP_SETTING_PATH = os.path.join(MAIN_PATH, 'app_settings', 'application_settings.config')

weapons_class_mapping = {
    'any' : None,
    'handgun': 0,
    'knife': 1,
    'none' : 'None'
}

clothings_class_mapping = {
    'sleeved_shirt' : 0,
    'sleeveless_top' : 1,
    'outwear' : 2,
    'shorts' : 3,
    'trousers' : 4,
    'skirt' : 5,
    'dress' : 6,
    'none' : 'None'
}

weapon_combobox_dict = {
    '0' : 'Any',
    '1' : 'Handgun',
    '2' : 'Knife',
    '3' : 'None'
}

upper_clothing_combobox_dict = {
    '0' : 'Sleeved Shirt',
    '1' : 'Sleeveless Top',
    '2' : "Outwear",
    '3' : "Dress",
    '4' : "None"
}

lower_clothing_combobox_dict = {
    '0' : "Shorts",
    '1' : "Trousers",
    '2' : "Skirt", 
    '3' : "None"
}

upper_clothing_colors_combobox_dict = {
    '-1' : "No upper clothing chosen",
    '0' : "Red",
    '1' : "Blue",
    '2' : "Yellow",
    '3' : "Green",
    '4' : "Orange",
    '5' : "Purple",
    # '6' : "White",
    # '7' : "Grey",
    # "8" : "Black"
    '6' : "Grey/White",
    '7' : "Black"
}

lower_clothing_colors_combobox_dict = {
    '-1' : "No lower clothing chosen",
    '0' : "Red",
    '1' : "Blue",
    '2' : "Yellow",
    '3' : "Green",
    '4' : "Orange",
    '5' : "Purple",
    # '6' : "White",
    # '7' : "Grey",
    # "8" : "Black"
    '6' : "Grey/White",
    '7' : "Black"
}


reversed_clothings_class_mapping = dict([(val, key) for key, val in clothings_class_mapping.items()])

### Prevents multithreading process to avoid conflict in resources
lock = threading.Lock()

### INITIALIZE DATABASE
db=sqlite3.connect('cctvapp.db')
cursor=db.cursor()

### CREATE TABLE FOR USER LOGIN IF DI PA NAGE-EXIST
create_user_table = """CREATE TABLE if not exists user_login_info(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_firstname VARCHAR,
        user_lastname VARCHAR,
        user_regname VARCHAR,
        user_email VARCHAR,
        user_password VARCHAR
        )"""
cursor.execute(create_user_table)
db.commit()

### CREATE OTP TABLE PARA MA AUTHENTICATE ANG MGA NASESEND NA OTP VIA EMAIL
create_reg_otp_table = """CREATE TABLE if not exists user_otp(
        otp_email VARCHAR,
        otp_current VARCHAR,
        otp_expire DEFAULT (datetime('now','localtime')) NOT NULL
        )"""
cursor.execute(create_reg_otp_table)
db.commit()

### CREATE TABLE AS TEMPORARY LALAGYANAN NG USER_LOGIN INFO
create_temp_table = """CREATE TABLE if not exists temp_user(
        user_firstname VARCHAR,
        user_lastname VARCHAR,
        user_regname VARCHAR,
        user_email VARCHAR,
        user_password VARCHAR,
        user_timestamp DEFAULT (datetime('now','localtime')) NOT NULL
        )"""
cursor.execute(create_temp_table)
db.commit()

### EMAIL IDENTIFIER
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

# Create the user_logs_directory folder if it doesn't exist
log_directory = "user_logs_directory"
os.makedirs(log_directory, exist_ok=True)

# Create the app_settings folder if it doesn't exist
appset_directory = "app_settings"
os.makedirs(appset_directory, exist_ok=True)

# JSON file path
json_file_path = os.path.join(log_directory, 'user_logs.json')

# Check if user_logs already exist
if not os.path.exists('user_logs_directory/user_logs.json'):
    # If the file doesn't exist, create it
    with open('user_logs_directory/user_logs.json', 'w') as json_file:
        json_file.write('{}')  # Writing an empty JSON object to the file

# Check if app_setting CONFIG already exist
if not os.path.exists('app_settings/application_settings.config'):
    # If the file doesn't exist, create it
    with open('app_settings/application_settings.config', 'w') as json_file:
        json_file.write('{}')  # Writing an empty CONFIG object to the file

# Configure the logging module
logging.basicConfig(level=logging.INFO,
                    format='%(message)s')

# Function to log user activities
def log_activity(username, activity, status, log_level=logging.INFO):
    timestamp = datetime.now().strftime('%b %d, %Y - %H:%M:%S')
    
    # Read existing JSON data from the file if it exists
    existing_data = {}
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            try:
                existing_data = json.load(json_file)
            except json.JSONDecodeError:
                pass

    # Create a log entry dictionary
    log_entry = {
        "timestamp": timestamp,
        "activity": activity,
        "status": status
    }

    # check if the username is in the DB
    cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (username,))
    check_logusername = cursor.fetchone()

    if check_logusername:
        # Check if the username already exists in the data
        if username in existing_data:
            existing_data[username].append(log_entry)
        else:
            # If the username doesn't exist, create a new entry for it
            existing_data[username] = [log_entry]

    # Save the updated data back to the JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

    # Check the log level and log accordingly
    if log_level == logging.INFO:
        logging.info(log_entry)

class LoginWindow(QMainWindow, Ui_Login):
    def __init__(self):
        super().__init__()
        self.ui=Ui_Login()
        self.setupUi(self)
        self.center()

        loginbtn = self.loginbutton
        loginbtn.clicked.connect(self.user_login)
        
        registerbtn = self.registertxt
        registerbtn.mouseReleaseEvent = self.registertxt_on_click
        resetbtn = self.forgotpasstxt
        resetbtn.mouseReleaseEvent = self.reset_on_click
        reveal_passbtn = self.revealpass
        reveal_passbtn.mouseReleaseEvent = self.toggle_pass_visibility

    def user_login(self):
        self.login_username = self.usernamelogin.text()
        login_userpass = self.passwordlogin.text()

        if (re.fullmatch(regex, self.login_username)):
                cursor.execute("SELECT * FROM user_login_info WHERE user_email=? and user_password=?", (self.login_username,login_userpass,))
                check_emaillogin = cursor.fetchall()
                
                if check_emaillogin:
                    cursor.execute("SELECT user_regname FROM user_login_info WHERE user_email=? and user_password=?", (self.login_username,login_userpass,))
                    check_emailpassuser = cursor.fetchone()
                    self.email_login_user = check_emailpassuser[0]

                    if check_emailpassuser:     
                        with lock:
                            logname = self.email_login_user
                            activity = "Successfully logged in using valid credentials."
                            logstatus = "SUCCESS"
                            log_activity(logname, activity, logstatus)
                            self.open_appwindow_ui = AppWindow(self.email_login_user)
                            self.close()
                            self.open_appwindow_ui.show()

                else:
                    cursor.execute("SELECT user_regname FROM user_login_info WHERE user_email=?", (self.login_username,))
                    check_emailpassuser = cursor.fetchone()
                    self.email_login_user = check_emailpassuser[0]
                    if check_emailpassuser:
                        logname = self.email_login_user
                        activity = "Failed Login Attempt using valid username/email address but invalid password."
                        logstatus = "FAILED"
                        log_activity(logname, activity, logstatus)
                        self.open_invlogin_ui = Invalid_login()
                        self.open_invlogin_ui.show()
        else: 
            ### FIND THE GIVEN CREDS SA DATABASE
            cursor.execute("SELECT * FROM user_login_info WHERE user_regname=? and user_password=?", (self.login_username,login_userpass,))
            check_login = cursor.fetchall()

            if check_login:
                logname = self.login_username
                activity = "Successfully logged in using valid credentials."
                logstatus = "SUCCESS"
                log_activity(logname, activity, logstatus)
                self.open_appwindow_ui = AppWindow(self.login_username)
                self.close()
                self.open_appwindow_ui.show()

            else:
                logname = self.login_username
                activity = "Failed login attempt using valid username/email address but invalid password."
                logstatus = "FAILED"
                log_activity(logname, activity, logstatus)
                self.open_invlogin_ui = Invalid_login()
                self.open_invlogin_ui.show()

    def center(self):

        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2-35
        self.move(x, y)

    ### REVEAL PASSWORD
    def toggle_pass_visibility(self,event):
        if self.passwordlogin.echoMode()==QLineEdit.EchoMode.Password:
            self.passwordlogin.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.passwordlogin.setEchoMode(QLineEdit.EchoMode.Password)

    ### REGISTER NOW PAGE CONNECTOR
    def registertxt_on_click(self, event):
        open_register_ui = RegisterWindow()
        open_register_ui.show()

    ### RESET PASSWORD PAGE CONNECTOR
    def reset_on_click(self, event):
        self.open_reset_ui = ResetWindow()
        self.open_reset_ui.show()

    ### ENABLE ENTER KEY SA KEYBOARD AS SUBMIT BUTTON
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return.value:
            self.user_login()


class DataWindow(QMainWindow, Ui_dataprivacy):
    def __init__(self):
        super().__init__()
        self.ui=Ui_dataprivacy()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.agreebtn = self.Proceed
        self.agreebtn.clicked.connect(self.on_agree_clicked)

        self.cancelagreebtn = self.Cancelagree
        self.cancelagreebtn.clicked.connect(self.cancelagreement)
        
        self.agreecheckBox.stateChanged.connect(self.update_submit_button_state)
        
        self.update_submit_button_state(self.agreecheckBox.checkState())
        
    def update_submit_button_state(self, state):
        if state == 2:  # 2 corresponds to Checked state
            self.agreebtn.setEnabled(True)
        else:
            self.agreebtn.setEnabled(False)
        
    def on_agree_clicked(self):
        self.close()
    
    def cancelagreement(self):
        all_windows = QApplication.topLevelWidgets()
        for window in all_windows:
            if not isinstance(window, LoginWindow):
                window.close()
            else:
                self.close()


class RegisterWindow(QMainWindow, Ui_Register):
    def __init__(self):
        super().__init__()
        self.ui=Ui_Register()
        self.setupUi(self)
        self.setMaximumSize(1000, 760)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.open_reset_ui = DataWindow()
        self.open_reset_ui.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.open_reset_ui.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.open_reset_ui.setParent(self)

        self.open_reset_ui.show()
        self.center_data_window()

        self.center() 

        submitbtn = self.registerbutton
        submitbtn.clicked.connect(self.register_user)
        logintxtbtn = self.loginheretxt
        logintxtbtn.mouseReleaseEvent = self.logintxt_on_click
        reveal_regpassbtn = self.revealregpass
        reveal_regpassbtn.mouseReleaseEvent = self.toggle_regpass_visibility
        reveal_regpassconfbtn = self.revealconfpass
        reveal_regpassconfbtn.mouseReleaseEvent = self.toggle_regpassconf_visibility

    def register_user(self):
        ins_userfirstn = self.userfirstanme.text().capitalize()
        ins_userlastn = self.userlastname.text().capitalize()
        ins_usern = self.usernamereg.text()
        self.ins_email = self.useremail.text()
        ins_passw = self.passwordreg.text()
        ins_passwcf = self.passwordregconf.text()

        first_name_length = len(self.userfirstanme.text())
        last_name_length = len(self.userlastname.text())
        email_length = len(self.useremail.text())
        username_length = len(self.usernamereg.text())
        password_length = len(self.passwordreg.text())

        if (password_length < 8 or
            not any(char.isupper() for char in ins_passw) or
            not re.search(r"[!@#$%^&*()\-_=+{};:,<.>]", ins_passw) or
            not any(char.isdigit() for char in ins_passw)):

            self.open_invalid_values_length_ui = Invalid_password_length()
            self.open_invalid_values_length_ui.show()
        
        elif username_length != 0 and username_length < 5:
            self.open_invalid_username_lengt_ui = Invalid_username_length()
            self.open_invalid_username_lengt_ui.show()
        
        elif email_length != 0 and email_length < 15:
            self.open_invalid_email_length_ui = Invalid_email_length()
            self.open_invalid_email_length_ui.show()

        elif last_name_length != 0 and last_name_length < 2:
            self.open_invalid_lastname_length_ui = Invalid_lastname_length()
            self.open_invalid_lastname_length_ui.show()
        
        elif first_name_length != 0 and first_name_length < 2:
            self.open_invalid_lastname_length_ui = Invalid_firstname_length()
            self.open_invalid_lastname_length_ui.show()

        else:
            if ins_userfirstn or ins_userlastn or ins_usern or self.ins_email or ins_passw or ins_passwcf:
            
                if ins_userfirstn and ins_userlastn:
                
                    if ins_usern:
                        ### CHECK IF NAG EEXIST NA YUNG USERNAME SA USER_LOGIN TABLE
                        cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (ins_usern,))
                        check_result = cursor.fetchone()

                        ### DELETE OLD RECORDS FROM TEMPORARY USER_LOGIN TABLE KAPAG 5 MINS OLD NA
                        current_time = datetime.now()
                        five_minutes_ago = current_time - timedelta(minutes=5)
                        cursor.execute("DELETE FROM temp_user WHERE user_timestamp <=?", (five_minutes_ago,))
                        db.commit()

                        ### VALIDATE IF NAG EEXIST  NA YUNG USERNAME
                        if check_result:
                            self.open_takenuser_ui = Invalid_taken_username()
                            self.open_takenuser_ui.show()

                        #### CHECK KUNG PAREHAS ANG PASSWORD GIVEN
                        else:
                            if ins_passw:
                                if ins_passw != ins_passwcf:
                                    self.open_invpass_ui = Invalid_conf_pass()
                                    self.open_invpass_ui.show()

                                ###  CHECK KUNG VALID EMAIL ADDRESS FORMAT ANG NILAGAY
                                else:
                                    if (re.fullmatch(regex, self.ins_email)):
                                        ### DAHIL VALID, ICHECK KUNG REGISTERED NA BA SA DATABASE ANG EMAIL
                                        cursor.execute("SELECT * FROM user_login_info WHERE user_email=?", (self.ins_email,))
                                        check_email= cursor.fetchone()

                                        if check_email:
                                            self.open_takenemail_ui = Invalid_taken_email()
                                            self.open_takenemail_ui.show()

                                        else:
                                            ###### EMAIL OTP SENDER ######
                                            smtp_server = 'smtp.gmail.com'
                                            smtp_port = 587  # Use the appropriate port for your SMTP server
                                            smtp_username = 'inquestai.recovery@gmail.com'
                                            smtp_password = 'yogtpfasxxxnofbn'
                                            sender_email = 'inquestai.recovery@gmail.com'
                                            recipient_email = self.ins_email
                                            subject = 'OTP FOR REGISTRATION - DO NOT SHARE'

                                            ###### OTP GENERATOR ######
                                            digits="ABCDEFGHIJK0123456789"
                                            OTP=""
                                            for i in range(6):
                                                OTP+=digits[math.floor(random.random()*21)]

                                            html_msg = """<h1>DO NOT SHARE TO ANYONE</h1>\n<h2>To continue your registration. Enter your One-Time Password to the application:</.>
                                                        <h4 style='text-align: center;'>---------------------------------------------------------------------------------------------------------------------------------------------------------------------------</h4>\n\n\n\n
                                                        <h1 style='text-align: center;'>{}</h1>\n
                                                        <h4 style='text-align: center;'>---------------------------------------------------------------------------------------------------------------------------------------------------------------------------</h4>\n\n\n\n

                                                        <i><b>IMPORTANT: The contents of this email and any attachments are confidential. It is strictly forbidden to share any part of this message with any third party, without a written consent of the sender. If you received this message by mistake, please reply to this message and follow with its deletion, so that we can ensure such a mistake does not occur in the future.</i></b>
                                                        """.format(OTP)

                                            # Create a MIMEText object with the HTML content
                                            html_part = MIMEText(html_msg, 'html')

                                            # Create a MIMEMultipart message
                                            message = MIMEMultipart()
                                            message['From'] = sender_email
                                            message['To'] = recipient_email
                                            message['Subject'] = subject

                                            # Attach the HTML content to the message
                                            message.attach(html_part)

                                            # Connect to the SMTP server and send the email
                                            try:
                                                server = smtplib.SMTP(smtp_server, smtp_port)
                                                server.starttls()  # Use TLS encryption
                                                server.login(smtp_username, smtp_password)
                                                server.sendmail(sender_email, recipient_email, message.as_string())
                                                server.quit()
                                            except Exception as e:
                                                print("Error sending email:", str(e))

                                            ### INSERT SA DATABASE UNG OTP AND EMAIL AS AUTHENTICATOR
                                            cursor.execute('INSERT INTO user_otp(otp_email, otp_current) VALUES (?,?)', (self.ins_email, OTP,))
                                            db.commit()

                                            ### CHECK THE CURRENT OTP SENT TO THE EMAIL
                                            cursor.execute("SELECT otp_expire FROM user_otp WHERE otp_email=?", (self.ins_email,))
                                            list_all_email = cursor.fetchall()
                                            highest = max(list_all_email)
                                            str_highest = str(highest[-1])
                                                #### THEN DELETE THE OLD ONES
                                            cursor.execute("DELETE FROM user_otp WHERE otp_expire <>? and otp_email=?;", (str_highest,self.ins_email,))
                                            db.commit()

                                            ### FROM THE USER INPUT NA EMAIL, ICHECK KUNG NAG EEXIST NA YUNG TEMPORARY RECORD
                                            cursor.execute("SELECT user_email FROM temp_user WHERE user_email=?", (self.ins_email,))
                                            check_temp_useremail= cursor.fetchone()

                                            ### IF NAG EEXIST NA, IUPDATE NA LANG YUNG RECORDS SA TEMPORAR TABLE
                                            if check_temp_useremail:
                                                cursor.execute('UPDATE temp_user SET  user_firstname=?, user_lastname=?, user_regname=?, user_email=?, user_password=? WHERE user_email=?', (ins_userfirstn, ins_userlastn, ins_usern, self.ins_email, ins_passw, self.ins_email,))
                                                db.commit()

                                            ### ELSE, IINSERT AS NEW
                                            else:
                                                cursor.execute('INSERT INTO temp_user(user_firstname, user_lastname, user_regname, user_email, user_password) VALUES (?,?,?,?,?)', (ins_userfirstn, ins_userlastn, ins_usern, self.ins_email, ins_passw,))
                                                db.commit()

                                            ### CALL NEXT WINDOW
                                            self.open_otp_ui = OTPRegWindow(self.ins_email)
                                            self.open_otp_ui.show()

                                    else:
                                        self.open_invemail_ui = Invalid_reg_email()
                                        self.open_invemail_ui.show()
                            else:
                                self.open_invblankpassreg_ui = Invalid_reg_blankpass()
                                self.open_invblankpassreg_ui.show()
                    else:
                        self.open_invblankpassreg_ui = Invalid_reg_blankusern()
                        self.open_invblankpassreg_ui.show()
                else:
                    self.open_invblankpassreg_ui = Invalid_reg_blankuserfullname()
                    self.open_invblankpassreg_ui.show()
            else:
                self.open_invblankpassreg_ui = Invalid_reg_blankreg()
                self.open_invblankpassreg_ui.show()
    
    def center(self):
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2-25
        self.move(x, y)

    def center_data_window(self):
        parent_geometry = self.geometry()
        data_window_geometry = self.open_reset_ui.geometry()
        x = parent_geometry.x() + (parent_geometry.width() - data_window_geometry.width()) // 2
        y = parent_geometry.y() + (parent_geometry.height() - data_window_geometry.height()) // 2
        self.open_reset_ui.move(x, y)

    def toggle_regpass_visibility(self,event):
        if self.passwordreg.echoMode()==QLineEdit.EchoMode.Password:
            self.passwordreg.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.passwordreg.setEchoMode(QLineEdit.EchoMode.Password)

    def toggle_regpassconf_visibility(self,event):
        if self.passwordregconf.echoMode()==QLineEdit.EchoMode.Password:
            self.passwordregconf.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.passwordregconf.setEchoMode(QLineEdit.EchoMode.Password)

    ### LOGIN PAGE CONNECTOR
    def logintxt_on_click(self, event):
        self.close()

    ### ENABLE ENTER KEY SA KEYBOARD AS SUBMIT BUTTON
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return.value:
            self.register_user()

class OTPRegWindow(QMainWindow, Ui_OTPWindow):
    def __init__(self,ins_email):
        super().__init__()
        self.ui=Ui_OTPWindow()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.conf_email = ins_email
        self.otpenter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confirm_otp = self.confirmotp
        confirm_otp.clicked.connect(self.check_otp_valid)

        cancel_otp = self.cancelreg
        cancel_otp.clicked.connect(self.cancelregwindow)

    ### VALIDATE OTP
    def check_otp_valid(self):
        otp_current_time = datetime.now()
        five_minutes_otp = otp_current_time - timedelta(minutes=5)
        cursor.execute("DELETE FROM user_otp WHERE otp_expire <=?", (five_minutes_otp,))
        db.commit()

        sent_otp = self.otpenter.text()

        ### CHECK IF NAG EEXIST YUNG OTP NA INPUT NI USER SA OTP TABLE
        cursor.execute("SELECT * FROM user_otp WHERE otp_current=? and otp_email=?", (sent_otp,self.conf_email,))
        check_otp_validity = cursor.fetchone()

        ### IF VALID, GET THE INFO BASED SA EMAIL NA NILAGAY
        if check_otp_validity:
            cursor.execute("SELECT * FROM temp_user WHERE user_email=?", (self.conf_email,))
            list_all_info = cursor.fetchall()

            ### ADD TO VARIABLES PARA MAILAGAY SA USER_LOGIN TABLE LATER
            if list_all_info:
                firstname, lastname, regname, email, password ,_ =  list_all_info[0]

                ### CHECK IF EXPIRED NA YUNG OTP 60 SECONDS
                cursor.execute("SELECT otp_expire FROM user_otp WHERE otp_current=?", (sent_otp,))
                check_otp_expiry = cursor.fetchone()
                datevalue_otp = check_otp_expiry[0]
                date_format = '%Y-%m-%d %H:%M:%S'
                new_datetype = datetime.strptime(datevalue_otp,date_format)
                updated_duration = new_datetype+timedelta(minutes=1)
                checktime_now = datetime.now()

                ### DELETE EXPIRED OTPs
                if updated_duration < checktime_now:
                    cursor.execute("DELETE FROM user_otp WHERE otp_current=?", (sent_otp,))
                    db.commit()

                    cursor.execute("DELETE FROM temp_user WHERE user_email=?", (self.conf_email,))
                    db.commit()

                    with lock:
                        self.open_expired_ui = OTPexpired()
                        self.close()
                        self.open_expired_ui.show()

                ### ILIPAT YUNG NASA TEMP_USER TABLE TO USER_LOGIN TABLE IF AUTHENTICATED
                else:
                    cursor.execute('INSERT INTO user_login_info(user_firstname, user_lastname, user_regname, user_email, user_password) VALUES (?,?,?,?,?)', (firstname, lastname, regname, email, password,))
                    db.commit()
                    ### DELETE THE TEMP_USER RECORD AFTER ILIPAT
                    cursor.execute("DELETE FROM temp_user WHERE user_email=?", (self.conf_email,))
                    db.commit()
                    ### DELETE THE USED OTP
                    cursor.execute("DELETE FROM user_otp WHERE otp_current=?", (sent_otp,))
                    db.commit()

                    with lock:
                        self.open_success_ui = Success_Reg()
                        self.open_success_ui.show()

            else:
                self.open_failed_ui = Failed_reg()
                self.open_failed_ui.show()

        else:
            self.open_failed_ui = Failed_reg()
            self.open_failed_ui.show()

    def cancelregwindow(self):
        self.close()

    ### ENABLE ENTER KEY SA KEYBOARD AS SUBMIT BUTTON
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return.value:
            self.check_otp_valid()

class ResetWindow(QMainWindow, Ui_Reset):
    def __init__(self):
        super().__init__()
        self.ui=Ui_Reset()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        cancelbtn = self.cancelforgot
        cancelbtn.clicked.connect(self.cancel_on_click)
        searchbtn = self.searchforgot
        searchbtn.clicked.connect(self.search_on_click)

    def search_on_click(self):
        self.emailotp = self.forgotpassem.text()

        if (re.fullmatch(regex, self.emailotp)):
            ### CHECK IF THE INPUT IS IN EMAIL FORMAT
            cursor.execute("SELECT * FROM user_login_info WHERE user_email=?", (self.emailotp,))
            check_email= cursor.fetchone()
            if check_email:
                ###### EMAIL OTP SENDER ######
                 #################### DO NOT UNCOMMENT KAPAG DI PA NEED ITEST NA WALANG DATABASE INTERFACE
                        smtp_server = 'smtp.gmail.com'
                        smtp_port = 587  # Use the appropriate port for your SMTP server
                        smtp_username = 'inquestai.recovery@gmail.com'
                        smtp_password = 'yogtpfasxxxnofbn'
                        sender_email = 'inquestai.recovery@gmail.com'
                        recipient_email = self.emailotp
                        subject = 'OTP FOR PASSWORD RESET - DO NOT SHARE'

                        ###### OTP GENERATOR ######
                        digits="ABCDEFGHIJK0123456789"
                        OTP=""
                        for i in range(6):
                            OTP+=digits[math.floor(random.random()*21)]

                        html_msg = """<h1>DO NOT SHARE TO ANYONE</h1>\n<h2>To reset your password. Enter your One-Time Password to the application:</.>
                                     <h4 style='text-align: center;'>---------------------------------------------------------------------------------------------------------------------------------------------------------------------------</h4>\n\n\n\n
                                     <h1 style='text-align: center;'>{}</h1>\n
                                     <h4 style='text-align: center;'>---------------------------------------------------------------------------------------------------------------------------------------------------------------------------</h4>\n\n\n\n

                                     <i><b>IMPORTANT: The contents of this email and any attachments are confidential. It is strictly forbidden to share any part of this message with any third party, without a written consent of the sender. If you received this message by mistake, please reply to this message and follow with its deletion, so that we can ensure such a mistake does not occur in the future.</i></b>
                                     """.format(OTP)

                        # Create a MIMEText object with the HTML content
                        html_part = MIMEText(html_msg, 'html')

                        # Create a MIMEMultipart message
                        message = MIMEMultipart()
                        message['From'] = sender_email
                        message['To'] = recipient_email
                        message['Subject'] = subject

                        # Attach the HTML content to the message
                        message.attach(html_part)

                        # Connect to the SMTP server and send the email
                        try:
                            server = smtplib.SMTP(smtp_server, smtp_port)
                            server.starttls()  # Use TLS encryption
                            server.login(smtp_username, smtp_password)
                            server.sendmail(sender_email, recipient_email, message.as_string())
                            server.quit()
                        except Exception as e:
                            print("Error sending email:", str(e))

                        ### INSERT SA DATABASE UNG OTP AND EMAIL AS AUTHENTICATOR
                        cursor.execute('INSERT INTO user_otp(otp_email, otp_current) VALUES (?,?)', (self.emailotp, OTP,))
                        db.commit()

                        ### CHECK THE CURRENT OTP SENT TO THE EMAIL
                        cursor.execute("SELECT otp_expire FROM user_otp WHERE otp_email=?", (self.emailotp,))
                        list_all_email = cursor.fetchall()
                        highest = max(list_all_email)
                        str_highest = str(highest[-1])
                            #### THEN DELETE THE OLD ONES
                        cursor.execute("DELETE FROM user_otp WHERE otp_expire <>? and otp_email=?;", (str_highest,self.emailotp,))
                        db.commit()

                        with lock:
                            self.open_otp_ui = OTPResetWindow(self.emailotp)
                            self.close()
                            self.open_otp_ui.show()

            else:
                self.open_invalidemailreset_ui = Unregistered_email_reset()
                self.open_invalidemailreset_ui.show()

        else:
            self.open_invalidemailreset_ui = Invalid_email_reset()
            self.open_invalidemailreset_ui.show()
    
    def cancel_on_click(self):
        self.close()
    
class OTPResetWindow(QMainWindow, Ui_OTPResetWindow):
    def __init__(self,emailotp):
        super().__init__()
        self.ui=Ui_OTPResetWindow()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.conf_email = emailotp
        self.otpenterreset.setAlignment(Qt.AlignmentFlag.AlignCenter)

        confirm_otp = self.confirmotpreset
        confirm_otp.clicked.connect(self.check_otp_valid)

        cancelresetwin = self.cancelreset
        cancelresetwin.clicked.connect(self.closereset)

    ### VALIDATE OTP
    def check_otp_valid(self):
        otp_current_time = datetime.now()
        five_minutes_otp = otp_current_time - timedelta(minutes=5)
        cursor.execute("DELETE FROM user_otp WHERE otp_expire <=?", (five_minutes_otp,))
        db.commit()

        sent_otp = self.otpenterreset.text()

        ### CHECK IF NAG EEXIST YUNG OTP NA INPUT NI USER SA OTP TABLE
        cursor.execute("SELECT * FROM user_otp WHERE otp_current=? and otp_email=?", (sent_otp,self.conf_email,))
        check_otp_validity = cursor.fetchone()

        ### IF VALID, GET THE INFO BASED SA EMAIL NA NILAGAY
        if check_otp_validity:
            ### CHECK IF EXPIRED NA YUNG OTP 60 SECONDS
                cursor.execute("SELECT otp_expire FROM user_otp WHERE otp_current=?", (sent_otp,))
                check_otp_expiry = cursor.fetchone()
                datevalue_otp = check_otp_expiry[0]
                date_format = '%Y-%m-%d %H:%M:%S'
                new_datetype = datetime.strptime(datevalue_otp,date_format)
                updated_duration = new_datetype+timedelta(minutes=1)
                checktime_now = datetime.now()

                ### DELETE EXPIRED OTPs
                if updated_duration < checktime_now:
                    cursor.execute("DELETE FROM user_otp WHERE otp_current=?", (sent_otp,))
                    db.commit()

                    cursor.execute("DELETE FROM temp_user WHERE user_email=?", (self.conf_email,))
                    db.commit()

                    with lock:
                        self.open_expired_ui = OTPexpired()
                        self.close()
                        self.open_expired_ui.show()

                ### Open Update password UI
                else:
                    self.open_success_ui = Reset_pass(self.conf_email)
                    self.close()
                    self.open_success_ui.show()
            
        else:
            self.open_failedreset_ui = Failed_reset()
            self.open_failedreset_ui.show()

    def closereset(self):
        self.close()

class Reset_pass(QMainWindow, Ui_ResetPassWindow):
    def __init__(self, conf_email):
        super().__init__()
        self.ui=Ui_MainWindow()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.shared_email = conf_email
        submit_newpass = self.update_newpass
        submit_newpass.clicked.connect(self.submit_newpassword)

        cancel_newpass = self.passcancelreset
        cancel_newpass.clicked.connect(self.cancelwindowpass)

        reveal_newpassbtn = self.newpassreveal
        reveal_newpassbtn.mouseReleaseEvent = self.toggle_regpass_visibility
        reveal_newconfbtn = self.confpassreveal
        reveal_newconfbtn.mouseReleaseEvent = self.toggle_regpassconf_visibility
    
    def submit_newpassword(self):
        getpass = self.newpass.text()
        getconfpass = self.confirm_newpass.text()
        password_length = len(self.newpass.text())

        if (password_length < 8 or
            not any(char.isupper() for char in getpass) or
            not re.search(r"[!@#$%^&*()\-_=+{};:,<.>]", getpass) or
            not any(char.isdigit() for char in getpass)):

            self.open_invalid_values_length_ui = Invalid_password_length()
            self.open_invalid_values_length_ui.show()
        else:
            if getpass:
                if getpass == getconfpass:
                    cursor.execute('UPDATE user_login_info SET user_password=? WHERE user_email=?', (getpass, self.shared_email,))
                    db.commit()

                    cursor.execute("DELETE FROM user_otp WHERE otp_email=?", (self.shared_email,))
                    db.commit()

                    with lock:
                        cursor.execute("SELECT user_regname FROM user_login_info WHERE user_email=?", (self.shared_email,))
                        check_emailpassuser = cursor.fetchone()
                        self.email_login_user = check_emailpassuser[0]
                        if check_emailpassuser:
                            logname = self.email_login_user
                            activity = "Successful password reset."
                            logstatus = "SUCCESS"
                            log_activity(logname, activity, logstatus)
                            self.open_successreset_ui = Reset_success()
                            self.open_successreset_ui.show()

                else:
                    cursor.execute("SELECT user_regname FROM user_login_info WHERE user_email=?", (self.shared_email,))
                    check_emailpassuser = cursor.fetchone()
                    self.email_login_user = check_emailpassuser[0]
                    if check_emailpassuser:
                        logname = self.email_login_user
                        activity = "Unsuccessful password reset."
                        logstatus = "FAILED"
                        log_activity(logname, activity, logstatus)
                        self.open_failedreset_ui = Reset_conf_pass()
                        self.open_failedreset_ui.show()
            else:
                self.open_failedresetblank_ui = Reset_blank_pass()
                self.open_failedresetblank_ui.show()

    def cancelwindowpass(self):
        self.close()
        
    def toggle_regpass_visibility(self,event):
        if self.newpass.echoMode()==QLineEdit.EchoMode.Password:
            self.newpass.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.newpass.setEchoMode(QLineEdit.EchoMode.Password)

    def toggle_regpassconf_visibility(self,event):
        if self.confirm_newpass.echoMode()==QLineEdit.EchoMode.Password:
            self.confirm_newpass.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.confirm_newpass.setEchoMode(QLineEdit.EchoMode.Password)

class StartProcessWorkerThread(QThread):

    processing_finished = pyqtSignal(dict)  # Signal for determining if the thread/worker has finished
    progress_updated = pyqtSignal(int)  # Signal for determining if the progress bar value was updated

    # Initialization
    def __init__(self, input_video_filepaths, weapons_to_detect, clothings_to_detect_and_colors, username, input_filter_dict):
        super().__init__()
        self.input_video_filepaths = input_video_filepaths
        self.weapons_to_detect = weapons_to_detect
        self.clothings_to_detect_and_colors = clothings_to_detect_and_colors
        self.username = username
        self.input_filter_dict = input_filter_dict
    
    # Callback method or function that returns the value of the instance's isInterruptionRequested() - used for cancelling QThread instance
    def interrupt_thread(self):
        return self.isInterruptionRequested()

    # Run method that emits the resulting data after running the method run_main_driver_code()
    def run(self):
        table_data = self.run_main_driver_code()
        self.processing_finished.emit(table_data)

    # This method is ran by run() method which runs the imported main_driver_code() from another .py file
    def run_main_driver_code(self):
        user_specific_table_data = {'None' : None} # Initially set the variable to be returned after the process to an empty dict (can be anything actually)
        
        # Instead of returning something, I implemented a try-except statement
        # So that if I raised an exception from cwd.main_driver_code when self.interrupt_thread() == True, I can catch it here with the except keyword
        try:
            user_specific_table_data = cwd.main_driver_code(
                input_video_filepaths=self.input_video_filepaths,
                weapons_to_detect=self.weapons_to_detect,
                clothings_to_detect_and_colors=self.clothings_to_detect_and_colors,
                username=self.username,
                input_filter_dict=self.input_filter_dict,
                progress_callback=self.progress_updated,
                cancel_callback=self.interrupt_thread # Pass the interrupt_thread method or function
            )
        except Exception as e: 
            print(f"Cancel button clicked. Cancelling operation.")


        return user_specific_table_data
 
    # def run_main_driver_code(self):
    #     cwd.main_driver_code(
    #         input_video_filepath = self.input_video_filepath,
    #         weapons_to_detect = self.weapons_to_detect,
    #         clothings_to_detect_and_colors = self.clothings_to_detect_and_colors
    #     )

    #     with open(r'D:\pd2_app_new_ui\temp\table_data.json', 'r') as f:
    #         table_data = json.load(f)

    #     return table_data

class VideoFilterWorker(QThread):
    filtering_finished = pyqtSignal(list)

    def __init__(self, video_filepaths, input_start_unix, input_end_unix):
        super().__init__()
        self.video_filepaths = video_filepaths
        self.input_start_unix = input_start_unix
        self.input_end_unix = input_end_unix
    
    def run(self):
        filtered_video_filepaths = []

        for fp in self.video_filepaths: # Iterate through each .mp4 video file

            # Try and look for media created
            try:
                properties = propsys.SHGetPropertyStoreFromParsingName(fp.replace('/', '\\'))
                dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
                dt = datetime.fromtimestamp(dt.timestamp())
            # If does not exist, ignore it and consider the next file
            except Exception as error:
                print(f"Error: {error} | Continuing video file filtering")
                continue

            fp_media_created_utc = dt
            fp_media_created_unix = fp_media_created_utc.timestamp() # UNIX formatted timestamp of fp_created_utc
            video_end_unix = fp_media_created_unix + VideoFileClip(fp).duration
            # print(
            #     f"Video End Unix: {video_end_unix}\nCreated Unix: {fp_media_created_unix}\nInput End: {input_end_unix}\nInput Start: {input_start_unix}\ndt: {dt.timestamp()}"
            # )
            
            # Ensure that datetime created is way past the datetime modified
            # datetime created > datetime modified means that the file is a copy, not the original
            if video_end_unix > fp_media_created_unix:
                # If the timerange of the .mp4 video is inside the input timerange, append the video filepath to filtered_video_filepaths
                # print((input_start_unix <= fp_created_unix) and (fp_modified_unix <= input_end_unix))
                if (self.input_start_unix <= fp_media_created_unix) and (video_end_unix <= self.input_end_unix):
                    filtered_video_filepaths.append(fp)
            # Else statement for troubleshooting - to see if the current filepath being iterated created datetime is way past its modified datetime
            else:
                print(f'{fp} created datetime is ahead of  its end date and timestamp')

        self.filtering_finished.emit(filtered_video_filepaths)


class AppWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, login_username):
        super().__init__()
        self.ui=Ui_MainWindow()
        self.setupUi(self)
        self.center()

        self.recent_input_filt_dict = None
        
        self.resultsFrame.setVisible(False)
        self.emptyDetsPlaceholder.setVisible(True)
        self.detectionProcessStart_invisible.setVisible(True) # Hidden but important for playing the correct video upon double-clicking in results table
        font = QFont()
        font.setPointSize(15)
        self.emptyDetsLbl.setFont(font)
        self.emptyDetsLbl.setText(
            "Provide your inputs on the section above:\
            \n\n⦿ Directory or folder containing all the archived footages or videos\
            \n⦿ Start and End Date Time to filter the video clips inside the chosen directory\
            \n⦿ Weapon to detect\
            \n⦿ Upper Clothing to detect and its corresponding color\
            \n⦿ Lower Clothing to detect and its corresponding color\
            \n⦿ After ensuring all inputs, click Start button to initialize the process and wait until it is finished"
        )

        self.get_userame = login_username
        self.worker = None
        self.detection_limit_to_display = 5 # Attribute for capping the number of detections to display in self.history_table
        self.detectionsaver.setText('5') # Set to 5 by default


        # Put this on main.py
        self.tableWidget.setColumnWidth(0, 180) # 200
        self.tableWidget.setColumnWidth(1, 180) # 900
        self.tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tableWidget.verticalHeader().setStretchLastSection(True)
        self.userlogs_table.setColumnCount(4)  # Four columns for Timestamp, Username, Message, and Status
        self.userlogs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.userlogs_table.setHorizontalHeaderLabels(["Timestamp", "Username", "Message", "Status"])
        self.userlogs_table.verticalHeader().setVisible(False)
        self.userlogs_table.setColumnWidth(0, 200)
        self.userlogs_table.setColumnWidth(1, 173) 
        self.userlogs_table.setColumnWidth(2, 560) 
        self.userlogs_table.setColumnWidth(3, 120)
        self.userlogs_table.horizontalHeader().setStretchLastSection(True)
        self.userlogs_table.horizontalHeader().setHighlightSections(False)
        self.userlogs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.max_rows = 200
        json_logsfilename = 'user_logs_directory/user_logs.json'
        self.populate_userlogs_table(self.load_json_data(json_logsfilename))

        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setColumnWidth(0, 300)
        self.history_table.setColumnWidth(1, 300) 
        # self.history_table.setColumnWidth(2, 560)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setHighlightSections(False)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.saved_table.verticalHeader().setVisible(False)
        self.saved_table.setColumnWidth(0, 300)
        self.saved_table.setColumnWidth(1, 300) 
        self.saved_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.saved_table.horizontalHeader().setStretchLastSection(True)
        self.saved_table.horizontalHeader().setHighlightSections(False)
        self.saved_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.populate_saved_clips()

        self.cancelbutton.setHidden(True)
        self.progressBar.setHidden(True) # Intiallly hide progress bar, only show Start Button
        self.cancelbutton.clicked.connect(self.cancel_detection_process)

        
        self.saved_table.itemDoubleClicked.connect(self.on_saved_clips_table_item_double_clicked) # Signal for double-clicked row in saved_table
        self.upperbox.currentIndexChanged.connect(self.upperbox_current_index_changed)
        self.lowerbox.currentIndexChanged.connect(self.lowerbox_current_index_changed)

        cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.get_userame,))
        list_name = cursor.fetchall()

        if list_name:
                _, firstname, lastname, regname, email, password=  list_name[0]
                updatemainname = firstname + ' ' + lastname
                self.username.setText(updatemainname)
                updatelogusername = '@' + regname
                self.userloginname.setText(updatelogusername)
                self.actsetfirstname.setText(firstname)
                self.actsetllastname.setText(lastname)
                self.usernameupdate.setText(regname)
                self.acctsetemail.setText(email)

        #################### Updating date #################### 

        self.central_widget = QLabel(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)  # Update every 1000 ms (1 second)
        self.update_clock()

        current_date_main = datetime.now()
        day_of_week = current_date_main.weekday()
        formatted_date = current_date_main.strftime(f", %d %B %Y | ")

        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        self.dayofweek = weekdays[day_of_week]
        self.datetoday = formatted_date
        self.update_time_date()

        self.selectArchivePathButton.clicked.connect(self.change_archive_path)
        self.startbutton.clicked.connect(self.start_process_read_input_filter_video)

        self.selectExportPathButton.clicked.connect(self.change_export_path)

        # self.tableWidget.cellDoubleClicked.connect(self.table_cell_clicked)

        self.history_table.itemDoubleClicked.connect(self.update_main_table_content)

        #### Read config settings ###
        self.configuration = {}
        if os.path.exists(USER_APP_SETTING_PATH):  # Check if the file exists
            try:
                with open(USER_APP_SETTING_PATH, 'r') as jsonset_file:
                    existing_appsetdata = json.load(jsonset_file)  # Load JSON data

                    user_settings = self.get_userame

                    if user_settings in existing_appsetdata:
                        appsettingexport_paths = [entry["export_path"] for entry in existing_appsetdata[user_settings]]
                        currentchecker = appsettingexport_paths[0]
                        if os.path.exists(currentchecker):
                            self.exportpath.setText(", ".join(appsettingexport_paths))
                            appsettinghis_detect = [entry["his_detect"] for entry in existing_appsetdata[user_settings]]
                            self.detectionsaver.setText(", ".join(appsettinghis_detect))
                            # Set the value of self.detection_limit_display with the integer casted text value of self.detectionsaver
                            self.detection_limit_to_display = int(self.detectionsaver.text())
                        else:
                            os.makedirs(currentchecker, exist_ok=True)
                    else:
                        user_home = os.path.expanduser("~")
                        videos_folder = os.path.join(user_home, "Videos")
                        save_directory = "InquestAI_Saved_Videos"
                        if self.get_userame != 0:
                            folder_path = os.path.join(videos_folder, save_directory, self.get_userame)
                            if (os.path.exists(folder_path)):
                                pass
                            else:
                                os.makedirs(folder_path, exist_ok=True)

                                export_data = {"export_path": folder_path, "his_detect":"5"}
                                existing_appsetdata[user_settings] = [export_data]

                                for key, value in existing_appsetdata.items():
                                    for item in value:
                                        if "export_path" in item:
                                            item["export_path"] = item["export_path"].replace("\\", "/")

                                # Write the updated configuration back to the JSON file
                                with open(USER_APP_SETTING_PATH, 'w') as file:
                                    json.dump(existing_appsetdata, file, indent=4)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        
        # Initialize the displayed number of recent detections
        self.update_display_num_of_recent_detections() 

        # Initialize the contents of self.history_table if table_data.json exists in the TEMP_OUTPUT_PATH
        if os.path.exists(os.path.join(TEMP_OUTPUT_PATH, 'table_data.json')):
            self.populate_history_table()

        ##################### Main window buttons ####################

        logoubtn = self.logoutwidget
        logoubtn.mouseReleaseEvent = self.user_logout

        homebtn = self.homewidget
        homebtn.mouseReleaseEvent = self.homebtnpage

        settingbtn = self.setingswidget
        settingbtn.mouseReleaseEvent = self.settingbtnpage

        historybtn = self.historywidget
        historybtn.mouseReleaseEvent = self.historybtnpage

        savedbtn = self.clippedwidget
        savedbtn.mouseReleaseEvent = self.savedbtnpage

        logsbtn = self.logswidget
        logsbtn.mouseReleaseEvent = self.logsbtnpage

        helpbtn = self.helpwidget
        helpbtn.mouseReleaseEvent = self.helpbtnpage

        aboutbtn = self.aboutwidget
        aboutbtn.mouseReleaseEvent = self.aboutbtnpage

        actsavechanges = self.saveactset
        actsavechanges.mouseReleaseEvent = self.updateactset

        updatepassword = self.updatepasswordset
        updatepassword.clicked.connect(self.updatepasswordsetting)

        application_settings = self.saveappset
        application_settings.clicked.connect(self.saveappsettings)

        self.folderexpoortname = 0

    def update_time_date(self):
        self.ddayofweek.setText(self.dayofweek)
        self.dcurrentdated.setText(self.datetoday)

        self.sdayofweek.setText(self.dayofweek)
        self.scurrentdated.setText(self.datetoday)

        self.hdayofweek.setText(self.dayofweek)
        self.hcurrentdated.setText(self.datetoday)

        self.cdayofweek.setText(self.dayofweek)
        self.ccurrentdated.setText(self.datetoday)

        self.ldayofweek.setText(self.dayofweek)
        self.lcurrentdated.setText(self.datetoday)

        self.h2dayofweek.setText(self.dayofweek)
        self.h2currentdated.setText(self.datetoday)

        self.adayofweek.setText(self.dayofweek)
        self.acurrentdated.setText(self.datetoday)

    def update_clock(self):
        current_datetime = QDateTime.currentDateTime()
        self.formatted_time = current_datetime.toString("hh:mm:ss")
        self.htime.setText(self.formatted_time)
        self.ctime.setText(self.formatted_time)
        self.ltime.setText(self.formatted_time)
        self.atime.setText(self.formatted_time)
        self.h2time.setText(self.formatted_time)
        self.dtime.setText(self.formatted_time)
        self.stime.setText(self.formatted_time)

    def homebtnpage(self, event):
        self.stackedWidget.setCurrentIndex(0)

    def settingbtnpage(self, event):
        with open(USER_APP_SETTING_PATH, 'r') as jsonset_file:
            existing_appsetdata = json.load(jsonset_file)  # Load JSON data

            user_settings = self.get_userame

            if user_settings in existing_appsetdata:
                appsettingexport_paths = [entry["export_path"] for entry in existing_appsetdata[user_settings]]
                self.exportpath.setText(", ".join(appsettingexport_paths))
                appsettinghis_detect = [entry["his_detect"] for entry in existing_appsetdata[user_settings]]
                self.detectionsaver.setText(", ".join(appsettinghis_detect))
                # Set the value of self.detection_limit_display with the integer casted text value of self.detectionsaver
                self.detection_limit_to_display = int(self.detectionsaver.text()) 
        self.stackedWidget.setCurrentIndex(1)
    
    def historybtnpage(self, event):
        self.stackedWidget.setCurrentIndex(2)
    
    def savedbtnpage(self, event):
        self.populate_saved_clips()
        self.stackedWidget.setCurrentIndex(3)

    def logsbtnpage(self, event):
        json_logsfilename = 'user_logs_directory/user_logs.json'
        self.populate_userlogs_table(self.load_json_data(json_logsfilename))
        self.stackedWidget.setCurrentIndex(4)

    def helpbtnpage(self, event):
        self.stackedWidget.setCurrentIndex(5)

    def aboutbtnpage(self, event):
        self.stackedWidget.setCurrentIndex(6)

    def updatepasswordsetting(self):
        self.open_logut_ui = change_pass(self.get_userame)
        self.open_logut_ui.show()

    # Load json file
    def load_json_data(self, path):
        try:
            with open(path, 'r') as json_file:
                data = json.load(json_file)
            return data
        except Exception as e:
            print(f"Error loading JSON data: {str(e)}")
            return []
    
    def upperbox_current_index_changed(self, index):
        if index == 4:
            self.upcolorbox.setDisabled(True)
        else:
            self.upcolorbox.setDisabled(False)
    
    def lowerbox_current_index_changed(self, index):
        if index == 3:
            self.lowercolorbox.setDisabled(True)
        else:
            self.lowercolorbox.setDisabled(False)
    
    # Double-clicked slot/handler when a row is clicked from saved_table - opens Windows File Explorer and highlights the selected file
    def on_saved_clips_table_item_double_clicked(self, item):
        row = item.row() # Get selected row
        filename = self.saved_table.item(row, 1).text() # Get the filename
        directory_saved = self.saved_table.item(row, 4).text() # Get the directory_saved
        filepath_to_be_redirected = os.path.join(directory_saved, filename).replace('/', '\\') # Combine the filename and directory_saved to be a filepath
        if os.path.exists(filepath_to_be_redirected): ##check if the file still exist
            try:
                subprocess.Popen(['explorer', '/select,', filepath_to_be_redirected]) # Open Windows File Explorer and highlight the filepath
            except Exception as error:
                print(f"Redirection to selected filepath clip failed: {error}")
        else:
            self.open_invalidsavepath_ui = deleted_saved()
            self.open_invalidsavepath_ui.show()


    def populate_userlogs_table(self, data):
        ###################################################################################
        #################### Filter .json file to delete old activity logs ################
        # Calculate the date 6 months ago from the current date
        six_months_ago = datetime.now() - timedelta(days=180)

        # Filter and remove records older than 6 months for each username
        for username, entries in data.items():
            data[username] = [entry for entry in entries if (
                entry.get("timestamp") and
                datetime.strptime(entry["timestamp"], '%b %d, %Y - %H:%M:%S') >= six_months_ago
            )]
        
        #Write the updated data back to the JSON file
        with open(r'user_logs_directory/user_logs.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
        ##################################################################################
        # Filter dictionary with same value of self.get_username
        username = self.get_userame

        user_data = data.get(username, [])  # Get log entries for the specific username

        #sort descending order
        user_data.sort(key=lambda x: QDateTime.fromString(x.get("timestamp", ""), 'MMM dd, yyyy - HH:mm:ss'), reverse=True)

        rowcountlogs = len(user_data)
        self.userlogs_table.setRowCount(rowcountlogs)

        for row, item in enumerate(user_data[:self.max_rows]):
            timestamp = QTableWidgetItem(item.get("timestamp", ""))
            username = QTableWidgetItem(username)
            activity = QTableWidgetItem(item.get("activity", ""))
            status = QTableWidgetItem(item.get("status", ""))

            self.userlogs_table.setItem(row, 0, timestamp)
            self.userlogs_table.setItem(row, 1, username)
            self.userlogs_table.setItem(row, 2, activity)
            self.userlogs_table.setItem(row, 3, status)

    def populate_saved_clips(self):
        savedclips_directory = "saved_videos"
        os.makedirs(savedclips_directory, exist_ok=True)
        self.clips_file_path = os.path.join(savedclips_directory, 'savedclips.json')
        self.clipped = {}
        if os.path.exists(self.clips_file_path):
            with open(self.clips_file_path, 'r') as file:
                self.clipped = json.load(file)

        username = self.get_userame

        user_data = self.clipped.get(username, [])

        #sort descending order
        user_data.sort(key=lambda x: QDateTime.fromString(x.get("timestamp", ""), 'MMM dd, yyyy - HH:mm:ss'), reverse=True)

        rowcountlogs = len(user_data)
        self.saved_table.setRowCount(rowcountlogs)

        for row, item in enumerate(user_data[:self.max_rows]):
            # combobox_dict_data_sequence = [weapon_combobox_dict, upper_clothing_combobox_dict, upper_clothing_colors_combobox_dict, lower_clothing_combobox_dict, lower_clothing_colors_combobox_dict]
            # input_filter_dict_str = "\n".join([f"  \u2022 {key}: {combobox_data[str(value)]}\t" for (key, value), combobox_data in zip(dict(list(item.get("input_filter_dict").items())[2:]).items(), combobox_dict_data_sequence)])
            combobox_dict_data_sequence = [weapon_combobox_dict, upper_clothing_combobox_dict, upper_clothing_colors_combobox_dict, lower_clothing_combobox_dict, lower_clothing_colors_combobox_dict]
            input_filter_dict_items = list(item.get("input_filter_dict").items())[2:]
            input_filter_dict_str = ""
            for index, ((key, value), combobox_data) in enumerate(zip(input_filter_dict_items, combobox_dict_data_sequence)):
                if index == 2 or index == len(input_filter_dict_items) - 1:
                    # Check if the previous value is "3"
                    prev_value = input_filter_dict_items[index - 1][1]
                    # print(f"prev_value: {prev_value} {combobox_data}")
                    if (prev_value == 3) or (prev_value == 4):
                        input_filter_dict_str += f"  \u2022 {key}: N/A\t\n"
                        continue
                        
                
                input_filter_dict_str += f"  \u2022 {key}: {combobox_data[str(value)]}\t\n"
            
            input_filter_dict_str = "\n".join([f"  \u2022 {key}: {value}\t" for key, value in dict(list(item.get("input_filter_dict").items())[0:2]).items()]) + "\n" + input_filter_dict_str
            input_filter_items = QTableWidgetItem(f"\n{input_filter_dict_str}\n")

            filename = QTableWidgetItem(item.get("filename", ""))
            timestamp = QTableWidgetItem(item.get("timestamp", ""))
            duration = QTableWidgetItem(item.get("duration", ""))
            path = QTableWidgetItem(item.get("path", ""))

            self.saved_table.setItem(row, 0, input_filter_items)
            self.saved_table.setItem(row, 1, filename)
            self.saved_table.setItem(row, 2, timestamp)
            self.saved_table.setItem(row, 3, duration)
            self.saved_table.setItem(row, 4, path)

        # self.saved_table.resizeRowsToContents()
        # self.saved_table.resizeColumnsToContents()
            
        # self.saved_table.resizeRowToContents(0)
        # self.saved_table.resizeRowToContents(1)
        # self.saved_table.resizeRowToContents(2)
        # self.saved_table.resizeRowToContents(3)
            
        self.saved_table.resizeRowsToContents()

        self.saved_table.resizeColumnToContents(0)
        self.saved_table.resizeColumnToContents(1)
        self.saved_table.resizeColumnToContents(2)
        self.saved_table.resizeColumnToContents(3)

    # Method to populate or update the contents of history_table (QTableWidget)
    def populate_history_table(self):
        try:
            # Read JSON file containing all table data for all users
            with open(os.path.join(TEMP_OUTPUT_PATH, 'table_data.json'), 'r') as json_file:
                all_table_data_for_all_users = json.load(json_file)
        except Exception as e:
            print(f"Error in self.populate_history_table: {e}")

        # print(all_table_data_for_all_users)
        # print("="*30)
        
        # If the current user has existing detection history in the JSON file, populate/update the history_table with it
        if f'@{self.get_userame}' in all_table_data_for_all_users:
            # Get all table_data for a user and sort them based on the start timestamp when the detection process started

            user_specific_table_data = dict(sorted(all_table_data_for_all_users[f'@{self.get_userame}'].items(), key=lambda item: item[0].split('_')[0], reverse=True)) 

            start_end_datetime_list = list(user_specific_table_data.keys())
            start_end_datetime_list.sort(key=lambda x: datetime.strptime(x.split('_')[0], "%b %d, %Y - %H:%M:%S"))
            from itertools import groupby
            grouped = groupby(start_end_datetime_list, key=lambda x: x.split('_')[0])
            with_unique_start_datetime_latest_duplicate_retain = [max(group, key=lambda x: datetime.strptime(x.split('_')[1], "%b %d, %Y - %H:%M:%S")) for _, group in grouped]
            
            # If there is a set limit
            if self.detection_limit_to_display:
                # If the set limit is greater than the total number of all detections made the the user
                if int(self.detection_limit_to_display) > len(with_unique_start_datetime_latest_duplicate_retain):
                    num_of_detections_to_display_limit = len(with_unique_start_datetime_latest_duplicate_retain) # Set the limit of detection history to how many detections that user has made all time
                else:
                    num_of_detections_to_display_limit = self.detection_limit_to_display # Otherwise, set as is
            else: # If there is no set limit
                num_of_detections_to_display_limit = 5 # Set it to 5 by default

            # Total number of all detections made by the current user and set it as the number of rows to the history_table capped by num_of_detections_to_display_limit
            row_count = num_of_detections_to_display_limit
            self.history_table.setRowCount(row_count)

            # user_specific_table_data = dict(list(user_specific_table_data.items())[1:])
            # print(dict(list(dict(list(user_specific_table_data.items())[1:]).items())[:num_of_detections_to_display_limit]))
            
            
            capped_start_end_datetime_list = [i[0] for i in list(user_specific_table_data.items())[:num_of_detections_to_display_limit]]
            capped_start_end_datetime_list.sort(key=lambda x: datetime.strptime(x.split('_')[0], "%b %d, %Y - %H:%M:%S"))
            capped_grouped = groupby(start_end_datetime_list, key=lambda x: x.split('_')[0])
            capped_with_unique_start_datetime_latest_duplicate_retain = [max(group, key=lambda x: datetime.strptime(x.split('_')[1], "%b %d, %Y - %H:%M:%S")) for _, group in capped_grouped]
            print(capped_with_unique_start_datetime_latest_duplicate_retain)
            # Iterate through each of the detection processes made
            # enumerate(dict(list(dict(list(user_specific_table_data.items())[1:]).items())[:num_of_detections_to_display_limit]))
            # dict(list(user_specific_table_data.items())[:num_of_detections_to_display_limit])
            for row, process_datetime_range in enumerate(capped_with_unique_start_datetime_latest_duplicate_retain):
                # Set the self.recent_input_filt_dict to the input_filter_dict value inside the user_specific_table_data
                # This keeps track of what input_filter_dict to provide when a video gets clipped and saved
                # if process_datetime_range != "input_filter_dict":
                datetime_started = process_datetime_range.split('_')[0] # Get the start datetime
                datetime_ended = process_datetime_range.split('_')[1] # Get the end datetime
                # Calculate the duration by subtracting datetime_started and datetime_ended in UNIX format
                duration = datetime.strptime(datetime_ended, "%b %d, %Y - %H:%M:%S").timestamp() - datetime.strptime(datetime_started, "%b %d, %Y - %H:%M:%S").timestamp() 

                # Construct the row and add it to history_table
                self.history_table.setItem(row, 0, QTableWidgetItem(datetime_started))
                self.history_table.setItem(row, 1, QTableWidgetItem(datetime_ended))
                self.history_table.setItem(row, 2, QTableWidgetItem(f'{duration} seconds'))
    

    # Method to populate or update the contents of QTableWidget in Home section
    def update_main_table_content(self, item):

        row = item.row() # Get the row that was double clicked

        start_datetime_processed = self.history_table.item(row, 0).text() # Get the start_datetime_processed
        end_datetime_processed = self.history_table.item(row, 1).text()  # Get the end_datetime_processed

        self.detectionProcessStart_invisible.setText(start_datetime_processed)

        try:
            # Read JSON file containing all table data for all users
            with open(os.path.join(TEMP_OUTPUT_PATH, 'table_data.json'), 'r') as json_file:
                all_table_data_from_all_users = json.load(json_file)
        except Exception as e:
            print(f"Error in self.update_main_table_content: {e}")
        
        # Get all detections made the current user
        all_history_of_detections_table_data_for_specific_user = all_table_data_from_all_users[f'@{self.get_userame}']

        # Construct a dict as input to self.updateTableData()
        # It shall contain the table_data for the specific start and end datetime the video(s) was/were processed
        # And the start and end datetime themselves formatted as a single string
        # And the input_filter_dict of the detection made by the user
        user_specific_table_data = {
            'table_data' : all_history_of_detections_table_data_for_specific_user[f'{start_datetime_processed}_{end_datetime_processed}'],
            'start_end_datetime_processed' : f'{start_datetime_processed}_{end_datetime_processed}'
        }

        self.updateTableData(user_specific_table_data) # Populate or update the contents of the QTableWidget in Home section
        self.detectionProcessStart_invisible.setHidden(True)
        self.stackedWidget.setCurrentIndex(0) # Go the Home section
        
    def user_logout(self, event):
        logname = self.get_userame
        activity = "Successfully logged out."
        logstatus = "SUCCESS"
        log_activity(logname, activity, logstatus)
        self.open_logut_ui = user_logout()
        self.open_logut_ui.show()

    def updateactset(self, event):
        self.updatedfirstname = self.actsetfirstname.text().title()
        self.updatedlastname = self.actsetllastname.text().title()
        self.updatedemail = self.acctsetemail.text()
        self.getusername = self.usernameupdate.text()

        first_name_length = len(self.actsetfirstname.text())
        last_name_length = len(self.actsetllastname.text())
        email_length = len(self.acctsetemail.text())
        username_length = len(self.usernameupdate.text())

        total_length = first_name_length + last_name_length + email_length + username_length

        if total_length == 0:
            self.open_invalid_values_length_ui = Invalid_values_length()
            self.open_invalid_values_length_ui.show()
        
        elif username_length != 0 and username_length < 5:
            self.open_invalid_username_lengt_ui = Invalid_username_length()
            self.open_invalid_username_lengt_ui.show()
        
        elif email_length != 0 and email_length < 15:
            self.open_invalid_email_length_ui = Invalid_email_length()
            self.open_invalid_email_length_ui.show()

        elif last_name_length != 0 and last_name_length < 2:
            self.open_invalid_lastname_length_ui = Invalid_lastname_length()
            self.open_invalid_lastname_length_ui.show()
        
        elif first_name_length != 0 and first_name_length < 2:
            self.open_invalid_lastname_length_ui = Invalid_firstname_length()
            self.open_invalid_lastname_length_ui.show()

        else:
            if self.updatedemail or self.getusername:
                if (re.fullmatch(regex, self.updatedemail)):
                    cursor.execute("SELECT * FROM user_login_info WHERE user_email=?", (self.updatedemail,))
                    check_email= cursor.fetchone()

                    cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.getusername,))
                    check_currentusername = cursor.fetchone()
                    if check_email and check_currentusername:
                        self.open_invalidemailupdate_ui = Invalid_username_email()
                        self.open_invalidemailupdate_ui.show()

                    elif check_email:
                        self.open_invalidemailreset_ui = Invalid_email_update()
                        self.open_invalidemailreset_ui.show()
                    
                    elif check_currentusername:
                        self.open_invaliduserupdate_ui = Invalid_username_update()
                        self.open_invaliduserupdate_ui.show()

                    else:
                        self.open_passwindow_ui = updateacctpass(self.get_userame, self.updatedfirstname, self.updatedlastname, self.updatedemail, self.getusername, self.get_userame)
                        self.open_passwindow_ui.show()

                elif (re.fullmatch(regex, self.updatedemail)) and self.getusername:
                    cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.getusername,))
                    check_currentusername = cursor.fetchone()

                    if check_currentusername:
                        self.open_invaliduserupdate_ui = Invalid_username_update()
                        self.open_invaliduserupdate_ui.show()

                    else:
                        self.open_passwindow_ui = updateacctpass(self.get_userame, self.updatedfirstname, self.updatedlastname, self.updatedemail, self.getusername, self.get_userame)
                        self.open_passwindow_ui.show()

                elif  self.getusername:
                    cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.getusername,))
                    check_currentusername = cursor.fetchone()

                    if check_currentusername:
                        self.open_invaliduserupdate_ui = Invalid_username_update()
                        self.open_invaliduserupdate_ui.show()

                    else:
                        self.open_passwindow_ui = updateacctpass(self.get_userame, self.updatedfirstname, self.updatedlastname, self.updatedemail, self.getusername, self.get_userame)
                        self.open_passwindow_ui.show()

                else:
                    self.open_invalidemailreset_ui = Invalid_email_update()
                    self.open_invalidemailreset_ui.show()
                    
            elif self.updatedemail or self.getusername or self.updatedfirstname or self.updatedlastname:
                self.open_passwindow_ui = updateacctpass(self.get_userame, self.updatedfirstname, self.updatedlastname, self.updatedemail, self.getusername, self.get_userame)
                self.open_passwindow_ui.show()

    def center(self):

        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2-35
        self.move(x, y)
    
    def update_display_num_of_recent_detections(self):
        # Read saved table_data.json (contains all_table_data_for_all_users)
        try:
            with open(os.path.join(TEMP_OUTPUT_PATH, 'table_data.json'), 'r') as f:
                table_data = json.load(f)

            user_specific_table_data = table_data[f'@{self.get_userame}']

            # If limit was set
            if self.detection_limit_to_display:
                # If the set limit is greater than the detections made by the user in lifetime usage
                if int(self.detection_limit_to_display) > len(user_specific_table_data.keys()):
                    num_of_recent_detections = len(user_specific_table_data.keys()) # Set the num_of_recent_detections to the max detections made by the user
                else: 
                    num_of_recent_detections = self.detection_limit_to_display # Otherwise, set the limit value as is
            else:
                num_of_recent_detections = 5 # Else, set it to 5 by default

            self.recentdetectint.setText(f'({num_of_recent_detections})') # Change the displayed text in the QLineEdit
        except Exception as e:
            self.recentdetectint.setText(f'0') # Change the displayed text in the QLineEdit
            print(f"Error in: {e}")

    
    def cancel_detection_process(self):
        self.worker.requestInterruption()

    # Opens folder selection dialog box
    def change_archive_path(self):
        filename = QFileDialog.getExistingDirectory()
        self.pathtxt.setText(filename)

    def change_export_path(self):
        self.folderexpoortname = QFileDialog.getExistingDirectory()
        if self.folderexpoortname:
            self.exportpath.setText(self.folderexpoortname)
        else:
            self.dialog_cancelled()

    def dialog_cancelled(self):
        self.open_failedexport_ui = failed_exportpath()
        self.open_failedexport_ui.show()

    def settings_appsettings(self):
        settings_directory = "app_settings"
        os.makedirs(settings_directory, exist_ok=True)
        self.settings_file_path = os.path.join(settings_directory, 'application_settings.config')
        regexnum = r'\d+'  # Fix the regex pattern to match digits
        histdetect = self.detectionsaver.text()
        user_settings = self.get_userame
        self.configuration = {}  # Initialize configuration

        if os.path.exists(self.settings_file_path):
            with open(self.settings_file_path, 'r') as file:
                self.configuration = json.load(file)

        checker_data = [entry for entry in self.configuration.get(user_settings, []) if "export_path" in entry]

        if checker_data:
            existing_export_path = checker_data[0].get("export_path", "")
            export_data = {
                "export_path": self.folderexpoortname if self.folderexpoortname else existing_export_path,
                "his_detect": histdetect if histdetect else checker_data[0].get("his_detect", "")
            }
        else:
            export_data = {"export_path": self.folderexpoortname if self.folderexpoortname else "", "his_detect": histdetect if histdetect else ""}

        if re.fullmatch(regexnum, histdetect) and (int(histdetect) > 0):
            export_data["his_detect"] = histdetect
            if user_settings in self.configuration:
                # User already exists in the configuration, update the export path and hist_detect
                self.configuration[user_settings][0]["export_path"] = export_data["export_path"]
                self.configuration[user_settings][0]["his_detect"] = export_data["his_detect"]
                self.open_successapp_ui = Success_appset()
                self.open_successapp_ui.show()
            else:
                # User does not exist, create a new entry
                self.open_successapp_ui = Success_appset()
                self.open_successapp_ui.show()
                self.configuration[user_settings] = [export_data]
        else:
            self.open_invalidhis_ui = Failed_history()
            event = None
            self.settingbtnpage(event)
            self.open_invalidhis_ui.show()
    
    def saveappsettings(self):
        self.settings_appsettings()
        self.save_config()

    def load_config(self):
        try:
            with open(self.settings_file_path, 'r') as config_file:
                self.configuration = json.load(config_file)
        except FileNotFoundError:
            self.configuration = {}  # If the config file doesn't exist, create an empty config dictionary

    def save_config(self):
        try:
            with open(self.settings_file_path, 'w') as config_file:
                json.dump(self.configuration, config_file, indent=4)
            self.detection_limit_to_display = int(self.detectionsaver.text())
            self.populate_history_table()
            self.update_display_num_of_recent_detections()
        except Exception as e:
            print(f"An error occurred while saving the configuration: {e}")

        # Method that gets executed when a timestamp cell is double-clicked
    # Note: The timestamp cell is located on each sub-table widget on the second column
    def cell_double_clicked_handler(self, row, column, filepath, start_end_datetime_processed, input_filter_dict):
        if column == 0: # If the cell clicked was first column (Timestamp column)
            sub_table = self.sender()  # Create a sender
            if sub_table:
                item = sub_table.item(row, column) # Extract item
                if item:
                    content = item.text() # Convert timestamp (UTC format) to text

                    # cap = cv2.VideoCapture(filepath)
                    # total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) # Get number of frames
                    # fps = VideoFileClip(filepath).fps
                    # fps = cap.get(cv2.CAP_PROP_FPS) # Get fps
                    # duration = total_frames / fps # Calculate duration
                    duration = VideoFileClip(filepath).duration
                    # video_file_created_unix = datetime.fromtimestamp(os.path.getctime(filepath)).replace(tzinfo=pytz.timezone('Asia/Manila')).timestamp()
                    try:
                        properties = propsys.SHGetPropertyStoreFromParsingName(filepath.replace('/', '\\'))
                        dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
                        dt = dt.timestamp() - 2 # offset

                    except Exception as error:
                        print(f"Error: {error}")
                    video_file_created_unix = dt
                    # print(filepath, dt, dt.timestamp(), video_file_created_unix, datetime.fromtimestamp(vide))
                    video_end_timestamp_unix = video_file_created_unix + duration
                    # video_file_modified_unix = os.path.getmtime(filepath) # Get modified time (end time) in unix time format
                    # selected_timestamp_unix = datetime.fromtimestamp(datetime.strptime(content, "%Y-%m-%d %H:%M:%S").timestamp()).replace(tzinfo=pytz.timezone('Asia/Manila')).timestamp() # Parse the chosen/clicked timestamp then convert to unix time format
                    selected_timestamp_unix = datetime.strptime(content, "%Y-%m-%d %H:%M:%S").timestamp() # Parse the chosen/clicked timestamp then convert to unix time format
                    video_timestamp_seconds_position = duration - (video_end_timestamp_unix - selected_timestamp_unix) # Calculate the timestamp in second to which the video be played when opened
                    # print(video_file_modified_unix - video_end_timestamp_unix)
                    # print(f'{video_timestamp_seconds_position}th second')


                    # Read saved table_data.json (contains all_table_data_for_all_users)
                    with open(os.path.join(TEMP_OUTPUT_PATH, 'table_data.json'), 'r') as f:
                        table_data = json.load(f)
                    
                    # Create a container for the timestamp and group them to three: weapons, upper clothing, and lower clothing
                    timestamps_in_seconds_to_overlay = {
                        'weapons' : [],
                        'upper_clothing_and_colors' : [],
                        'lower_clothing_and_colors' : []
                    }

                    # If the video filepath exists in the table_data.json for a specific username and start and end datetime it was processed
                    if filepath in table_data[f'@{self.get_userame}'][start_end_datetime_processed]:
                        info = table_data[f'@{self.get_userame}'][start_end_datetime_processed][filepath] # Get the value (a dictionary) for the chosen filepath
                        for timestamp, contents in info.items(): # Iterate through each timestamp
                            if contents.get('weapons'): # Each timestamp is mapped to a list of weapons, get them
                                # print(duration, video_end_timestamp_unix, float(timestamp))
                                timestamp_position_in_seconds = duration - (video_end_timestamp_unix - float(timestamp)) # Get their timestamp
                                timestamps_in_seconds_to_overlay['weapons'].append(timestamp_position_in_seconds) # Add them to the weapon list in the dictionary
                            
                            clothing_and_colors = contents.get("clothing_and_colors") # Each timestamp is also mapped to a list of clothings with corresponding colors, get them
                            # print(clothing_and_colors, type(clothing_and_colors))
                            if clothing_and_colors: # If there are contents
                                for clothing_info in clothing_and_colors: # Iterate through each
                                    clothing_type = clothing_info[0] # Determine if it is upper_clothing or lower_clothing
                                    # Conditional
                                    if "upper_clothing" in clothing_type: # Add to upper_clothing list in the dictionary
                                        timestamp_position_in_seconds = duration - (video_end_timestamp_unix - float(timestamp))
                                        timestamps_in_seconds_to_overlay['upper_clothing_and_colors'].append(timestamp_position_in_seconds)
                                    elif "lower_clothing" in clothing_type: # Add to lower_clothing list in the dictionary
                                        timestamp_position_in_seconds = duration - (video_end_timestamp_unix - float(timestamp))
                                        timestamps_in_seconds_to_overlay['lower_clothing_and_colors'].append(timestamp_position_in_seconds)
                    
                    # Format the filename to get the correc video based on the current user and datetime the detection process started
                    further_formatted_start_detection_datetime = self.detectionProcessStart_invisible.text().replace(",", "-").replace(":", "-").strip().replace(" ", "-")
                    video_filename_without_file_fmt_suffix = filepath.split('\\')[-1].split('.mp4')[0] # Get filename
                    cleaned_userloginname = self.userloginname.text().replace('@', '')
                    video_filename = f'{video_filename_without_file_fmt_suffix}_-_{cleaned_userloginname}-_-{further_formatted_start_detection_datetime}.mp4'
                    temp_output_video_filepath = os.path.join(TEMP_OUTPUT_PATH, video_filename)
                    # print(video_filename)
                    # print(temp_output_video_filepath)
                    # Log the action
                    logname = self.get_userame
                    activity = "Viewed the video at the selected timestamp."
                    logstatus = "NORMAL"
                    log_activity(logname, activity, logstatus)
                    # Play the video with bounding boxes
                    # print(timestamps_in_seconds_to_overlay["lower_clothing_and_colors"])
                    self.videoplayer_ui = VideoPlayer(temp_output_video_filepath, math.floor(video_timestamp_seconds_position), self.get_userame, duration, self.exportpath.text(), input_filter_dict, timestamps_in_seconds_to_overlay) # Create VideoPlayer instance
                    self.videoplayer_ui.show() # Open VideoPlayer instance
    
    # Executed when Start Button is clicked
    # Reads input and starts the driver code for weapon and clothing detection and table data generation
    def start_process_read_input_filter_video(self):

        starttime_str = self.startDateTime.text()
        endtime_str = self.endDateTime.text()

        # Define the format for parsing
        date_format = '%b/%d/%Y %H:%M'

        # Parse the input times into datetime objects
        starttime = datetime.strptime(starttime_str, date_format)
        endtime = datetime.strptime(endtime_str, date_format)

        # Get value of dropdown
        self.weaponvar = self.WeaponBox.currentIndex()
        self.upperclothingvar = self.upperbox.currentIndex()
        self.lowerboxvar = self.lowerbox.currentIndex()
        self.uppercolorvar = self.upcolorbox.currentIndex()
        self.lowercolbox = self.lowercolorbox.currentIndex()

        if (self.weaponvar == 3) and (self.upperclothingvar == 4) and (self.lowerboxvar == 3):
            self.error_prompt_ui = DetectionProcessFailDialogBox_NeedAtLeastOne()
            self.error_prompt_ui.show()
            
        else:
            # Calculate the time difference
            time_difference = endtime - starttime

            invalid_vars = []

            if not os.path.exists(rf"{self.pathtxt.text()}"):
                invalid_vars.append("Invalid/Non-existing archive path")
            if self.weaponvar < 0:
                invalid_vars.append("Weapon")
            if self.upperclothingvar < 0:
                invalid_vars.append("Upper Clothing")
            if (self.upperbox.currentIndex() != 4) and (self.uppercolorvar < 0): # If not None and -1 is the current index
                invalid_vars.append("Upper Clothing Color")
            if self.lowerboxvar < 0:
                invalid_vars.append("Lower Clothing")
            if (self.lowerbox.currentIndex() != 3) and (self.lowercolbox < 0): # If not None and -1 is the current index
                invalid_vars.append("Lower Clothing Color")
                
            
            if invalid_vars:
                self.open_warning_ui = invalid_param(invalid_vars)
                self.open_warning_ui.show()
            else:
                # Check if the time difference is more than 1 hour
                if time_difference > timedelta(seconds=1):
                    self.disableEnableDetectionButtons(enabled=False) # Disable all necessary input widgets

                    # temp_latest_input_filter_dict_json_fp = os.path.join(TEMP_OUTPUT_PATH, 'temp_latest_input_filter_dict.json')
                    # os.makedirs(temp_latest_input_filter_dict_json_fp, exist_ok=True)
                    # with open(temp_latest_input_filter_dict_json_fp, 'w') as jfile:
                    #     json.dump(most_recent_input_filter_dict,)
                     

                    # Create a QProgressDialog to indicate that the videos in the selected directory are being filtered
                    self.progress_dialog = QProgressDialog("Reading input parameters and filtering videos", None, 0, 0, self)
                    self.progress_dialog.setWindowTitle("Loading - Please wait")
                    # self.progress_dialog.setAutoClose(True)

                    # Read and parse inputs
                    weapons_to_detect = [weapons_class_mapping[self.WeaponBox.currentText().lower()]] # list of integers based on weapons_class_mapping
                    upper_clothings_to_detect = [clothings_class_mapping['_'.join(self.upperbox.currentText().lower().split(' '))]] # list of integers based on clothings_class_mapping
                    lower_clothings_to_detect = [clothings_class_mapping['_'.join(self.lowerbox.currentText().lower().split(' '))]] # list of integers based on clothings_class_mapping
                    upper_clothings_color = self.upcolorbox.currentText().lower() # make it lower case
                    lower_clothings_color = self.lowercolorbox.currentText().lower() # make it lower case
                    input_videos_directory = rf'{self.pathtxt.text()}' # filepath string content of Archive Path input

                    # Dictionary mapping for the upper and clothing class with their corresponding chosen color.
                    clothings_to_detect_and_colors = {
                        reversed_clothings_class_mapping[upper_clothings_to_detect[0]] : upper_clothings_color,
                        reversed_clothings_class_mapping[lower_clothings_to_detect[0]] : lower_clothings_color
                    }

                    # Read and parse input date and time range
                    #Format - "%m/%d/%Y %I:%M %p"
                    # input_start_utc = datetime.strptime(f'{self.startDateTime.text()}', "%m/%d/%Y %I:%M %p").replace(tzinfo=pytz.timezone('Asia/Manila')) # Parse the start date and time (UTC format) and change the timezone to Asia/Manila
                    # input_end_utc = datetime.strptime(f'{self.endDateTime.text()}', "%m/%d/%Y %I:%M %p").replace(tzinfo=pytz.timezone('Asia/Manila')) # Parse the end date and time (UTC format) and change the timezone to Asia/Manila
                    # Format - "%b/%d/%Y %H:%M"
                    input_start_utc = datetime.strptime(f'{self.startDateTime.text()}', "%b/%d/%Y %H:%M") # Parse the start date and time (UTC format) and change the timezone to Asia/Manila
                    input_end_utc = datetime.strptime(f'{self.endDateTime.text()}', "%b/%d/%Y %H:%M") # Parse the end date and time (UTC format) and change the timezone to Asia/Manila
                    input_start_unix = input_start_utc.timestamp() # Convert the UTC formatted input start datetime to UNIX format
                    input_end_unix = input_end_utc.timestamp() # Convert the UTC formatted input end datetime to UNIX format

                    filtered_video_filepaths = [] # List that will contain the filtered filepaths
                    video_filepath_list = glob.glob(os.path.join(input_videos_directory, '*.mp4')) # List of .mp4 video files in the chosen directory
                    # for fp in video_filepath_list: # Iterate through each .mp4 video file

                    #     # Try and look for media created
                    #     try:
                    #         properties = propsys.SHGetPropertyStoreFromParsingName(fp.replace('/', '\\'))
                    #         dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
                    #         dt = datetime.fromtimestamp(dt.timestamp())
                    #     # If does not exist, ignore it and consider the next file
                    #     except Exception as error:
                    #         print(f"Error: {error} | Continuing video file filtering")
                    #         continue

                    #     fp_media_created_utc = dt
                    #     fp_media_created_unix = fp_media_created_utc.timestamp() # UNIX formatted timestamp of fp_created_utc
                    #     video_end_unix = fp_media_created_unix + VideoFileClip(fp).duration
                    #     # print(
                    #     #     f"Video End Unix: {video_end_unix}\nCreated Unix: {fp_media_created_unix}\nInput End: {input_end_unix}\nInput Start: {input_start_unix}\ndt: {dt.timestamp()}"
                    #     # )
                        
                    #     # Ensure that datetime created is way past the datetime modified
                    #     # datetime created > datetime modified means that the file is a copy, not the original
                    #     if video_end_unix > fp_media_created_unix:
                    #         # If the timerange of the .mp4 video is inside the input timerange, append the video filepath to filtered_video_filepaths
                    #         # print((input_start_unix <= fp_created_unix) and (fp_modified_unix <= input_end_unix))
                    #         if (input_start_unix <= fp_media_created_unix) and (video_end_unix <= input_end_unix):
                    #             filtered_video_filepaths.append(fp)
                    #     # Else statement for troubleshooting - to see if the current filepath being iterated created datetime is way past its modified datetime
                    #     else:
                    #         print(f'{fp} created datetime is ahead of  its end date and timestamp')
                    
                    # print(filtered_video_filepaths)
                    # print(weapons_to_detect)
                    # print(clothings_to_detect_and_colors)

                    self.video_filter_worker = VideoFilterWorker(video_filepath_list, input_start_unix, input_end_unix)
                    self.video_filter_worker.start()
                    callback_with_params = partial(self.start_process_run_driver_code, time_difference, weapons_to_detect, clothings_to_detect_and_colors)
                    self.video_filter_worker.filtering_finished.connect(callback_with_params)

                # =========================
                #     if len(filtered_video_filepaths) <= 0:
                #         #Pop up for no detection
                #         logname = self.get_userame
                #         activity = "Filter detection attempt initiated. No available videos to process."
                #         logstatus = "FAILED"
                #         log_activity(logname, activity, logstatus)
                #         self.open_faileddetect_ui = No_video_detect()
                #         self.open_faileddetect_ui.show()
                #     else:
                #         # Add user log that the process started
                #         if time_difference > timedelta(hours=1):
                #             self.open_warning_ui = warning_range()
                #             self.open_warning_ui.show()

                #         logname = self.get_userame
                #         activity = "Filter detection initiated. Video detection processed successfully."
                #         logstatus = "SUCCESS"
                #         log_activity(logname, activity, logstatus)
                #         self.progressBar.setValue(0) # Set/Initialize progress bar to 0%
                #         self.disableEnableDetectionButtons(enabled=False) # Disable all input widgets
                #         self.hideUnhideStartButtonAndProgressBar(show_start=False) # Hide Start Button and show Progress Bar
                #         self.worker = StartProcessWorkerThread(filtered_video_filepaths, weapons_to_detect, clothings_to_detect_and_colors, self.userloginname.text()) # Create thread worker instance and pass necessary parameters
                #         # Start running the thread worker instance to detectm generate table data, and update QTableWidget in main section with it
                #         self.worker.start() 
                #         # When the PyQt signal (progress_updated) gets updated from detect_weapon.py or detect_clothings.py, update the value of QProgressBar with the emitted value (detect_weapon.py - Line 255; detect_clothings.py - Line 290)
                #         self.worker.progress_updated.connect(self.updateProgressBar) 
                #         # When the PyQt signal (processing_finished) is finished, update the table data by executing self.updateTableData
                #         self.worker.processing_finished.connect(self.updateTableData) 
                #         # Enable input widgets after the thread worker is finished detecting and providing the table data
                #         self.worker.finished.connect(self.disableEnableDetectionButtons) 
                #         # Show Start Button again and hide the Progress Bar
                #         self.worker.finished.connect(self.hideUnhideStartButtonAndProgressBar) 
                #         # self.worker.processing_finished.connect(self.populate_history_table)
                #         # self.worker.processing_finished.connect(self.update_display_num_of_recent_detections)
                #         print(f"Is self.worker running? {self.worker.isRunning()}")
                #         self.worker.terminate()
                #         print(f"Request Interrupted: {self.worker.isInterruptionRequested()}")
                #         self.worker.requestInterruption()
                #         print(f"Request Interrupted: {self.worker.isInterruptionRequested()}")

                else:
                    self.open_warning_ui = invalid_dateparam()
                    self.open_warning_ui.show()

    def start_process_run_driver_code(self, time_difference, weapons_to_detect, clothings_to_detect_and_colors, filtered_video_filepaths):
        self.progress_dialog.close()

        if len(filtered_video_filepaths) <= 0:
                #Pop up for no detection
                logname = self.get_userame
                activity = "Filter detection attempt initiated. No available videos to process."
                logstatus = "FAILED"
                log_activity(logname, activity, logstatus)
                self.disableEnableDetectionButtons(enabled=True)
                self.open_faileddetect_ui = No_video_detect()
                self.open_faileddetect_ui.show()
        else:
            # Add user log that the process started
            if time_difference > timedelta(hours=1):
                self.open_warning_ui = warning_range()
                self.open_warning_ui.show()

            logname = self.get_userame
            activity = "Filter detection initiated. Video detection processed successfully."
            logstatus = "SUCCESS"
            log_activity(logname, activity, logstatus)


            input_filter_dict = {
                "start_datetime" : self.startDateTime.text(),
                "end_datetime" : self.endDateTime.text(),
                "weapons" : self.WeaponBox.currentIndex(),
                "upper_clothing" : self.upperbox.currentIndex(),
                "upper_clothing_color" : self.upcolorbox.currentIndex(),
                "lower_clothing" : self.lowerbox.currentIndex(),
                "lower_clothing_color" : self.lowercolorbox.currentIndex()
            }
            

            self.progressBar.setValue(0) # Set/Initialize progress bar to 0%
            # self.disableEnableDetectionButtons(enabled=False) # Disable all input widgets
            self.hideUnhideStartButtonAndProgressBar(show_start=False) # Hide Start Button and show Progress Bar
            self.worker = StartProcessWorkerThread(filtered_video_filepaths, weapons_to_detect, clothings_to_detect_and_colors, self.userloginname.text(), input_filter_dict) # Create thread worker instance and pass necessary parameters
            # Start running the thread worker instance to detectm generate table data, and update QTableWidget in main section with it
            self.worker.start()
            # When the PyQt signal (progress_updated) gets updated from detect_weapon.py or detect_clothings.py, update the value of QProgressBar with the emitted value (detect_weapon.py - Line 255; detect_clothings.py - Line 290)
            self.worker.progress_updated.connect(self.updateProgressBar)
            # When the PyQt signal (processing_finished) is finished, update the table data by executing self.updateTableData
            self.worker.processing_finished.connect(self.updateTableData)
            # Enable input widgets after the thread worker is finished detecting and providing the table data
            # Show Start Button again and hide the Progress Bar
            self.worker.finished.connect(self.hideUnhideStartButtonAndProgressBar) # Show Start Button and Hide Progress Bar again
            self.worker.finished.connect(self.disableEnableDetectionButtons) # Enable all necessary input parameter widgets again



    def empty_main_table(self):
        for _ in range(self.tableWidget.rowCount()):
            self.tableWidget.removeRow(0)

    # Updates the contents of QTableWidget based on the passed table data from the worker thread (i.e., from self.start_process())
    def updateTableData(self, user_specific_table_data):
        # print('\n\n\n')
        # print(table_data)
        # print(type(table_data))
        
        # self.empty_main_table()
        # print(f"self.recent_input_filt_dict -> {self.recent_input_filt_dict}")


        if len(user_specific_table_data) <= 0:
            self.success_no_detections_ui = DetectionProcessSuccess_NoDetections()
            self.success_no_detections_ui.show()
        elif (len(user_specific_table_data) == 1) and ('None' in user_specific_table_data):
            self.cancel_success_ui = DetectionProcessSuccess_NoDetections()
            self.cancel_success_ui.tofillupsuccess.setText("Detection process cancelled successfully.")
            self.cancel_success_ui.show()
        else:        
            self.empty_main_table() # Remove contents of the table before updating it

            table_data = user_specific_table_data['table_data']
            start_end_datetime_processed = user_specific_table_data['start_end_datetime_processed']

            self.recent_input_filt_dict = table_data["input_filter_dict"] # Set the current (recent) input_filter_dict which shall be used for updating saved videos table

            # Set the input filter widget values based on the input_filter_dict of the detection chosen to be displayed in the table
            start_datetime_qdatetime = QDateTime.fromString(table_data["input_filter_dict"]["start_datetime"], "MMM/dd/yyyy hh:mm")
            end_datetime_qdatetime = QDateTime.fromString(table_data["input_filter_dict"]["end_datetime"], "MMM/dd/yyyy hh:mm")
            self.startDateTime.setDateTime(start_datetime_qdatetime)
            self.endDateTime.setDateTime(end_datetime_qdatetime)
            weapon_idx = table_data["input_filter_dict"]["weapons"]
            upper_clothing_idx = table_data["input_filter_dict"]["upper_clothing"]
            lower_clothing_idx = table_data["input_filter_dict"]["lower_clothing"]
            upcolor_clothing_idx = table_data["input_filter_dict"]["upper_clothing_color"]
            lowercolor_clothing_idx = table_data["input_filter_dict"]["lower_clothing_color"]
            if weapon_idx > -1:
                self.WeaponBox.setCurrentIndex(weapon_idx)
            if upper_clothing_idx > -1:
                self.upperbox.setCurrentIndex(upper_clothing_idx)
            if lower_clothing_idx > -1:
                self.lowerbox.setCurrentIndex(lower_clothing_idx)
            if upcolor_clothing_idx > -1:
                self.upcolorbox.setCurrentIndex(upcolor_clothing_idx)
            if lowercolor_clothing_idx > -1:
                self.lowercolorbox.setCurrentIndex(lowercolor_clothing_idx)

            # Next three code lines are needed to play output video with bboxes when the results table gets updated/displayed in home section
            start_datetime_processed = start_end_datetime_processed.split('_')[0]
            further_formatted_start_detection_datetime = start_datetime_processed.replace(",", "-").replace(":", "-").strip().replace(" ", "-")
            self.detectionProcessStart_invisible.setText(further_formatted_start_detection_datetime)

            row = 0 # Initialize row = 0 (we will traverse from first to nth row depending on the length of table data)
            
            # print(f"BEFORE: {table_data.keys()}")
            input_filter_dict_pop = ('input_filter_dict', table_data.pop('input_filter_dict'))
            table_data.update([input_filter_dict_pop])
            # print(f"AFTER: {table_data.keys()}")

            for filepath, info in dict(list(table_data.items())[:-1]).items(): # Iterate through each filepath and corresponding dictionary value
                if len(info) > 0: # If the dictionary value has no contents (no detection data)

                    self.resultint.setText(str(len(info)))

                    self.tableWidget.insertRow(row) # Insert new row
                    self.tableWidget.setItem(row, 0, QTableWidgetItem(filepath)) # Set the new row's value column (i.e., Video Filepath) to the key

                    sub_table_widget = QTableWidget(len(info), 4) # Create a new sub-QTableWidget - this will insert to the second column
                    

                    for idx, (timestamp, items) in enumerate(info.items()): # Iterate the dictionary (i.e., info)
                        utc_timestamp = datetime.fromtimestamp(int(timestamp)) # Get the UTC formatted time from UNIX timestamp
                        timestamp_to_insert = QTableWidgetItem(str(utc_timestamp)) # Make a QTableWidgetItem from it
                        sub_table_widget.setItem(idx, 0, timestamp_to_insert) # Insert it to the first column of the sub QTableWidget

                        weapons_in_current_timestamp = [i[0] for i in items['weapons']] # Filter existing weapons in the current timestamp being iterated (Note: timestamps are the key in info dictionary)
                        weapons_to_insert = QTableWidgetItem(', '.join(list(set(weapons_in_current_timestamp)))) # Join the filtered weapons by comma
                        sub_table_widget.setItem(idx, 1, weapons_to_insert) # Insert it to the second column of the sub QTableWidget
                        
                        # A function to be added to each cell in the timestamp column of each sub-tablewidget
                        # Pass the row being clicked and always return 0 (Timestamp column) for the column. Include the corresponding filepath and start and end datetime processed as well
                        # Include the input_filter_dict as well so it can be passed to videoplayer.py (VideoPlayer() instance) for providing input_filt_dict to saved videos
                        
                        cell_double_click_lambda = lambda row=idx, column=0, filepath=filepath, start_end_datetime_processed=start_end_datetime_processed, input_filter_dict=self.recent_input_filt_dict: self.cell_double_clicked_handler(row, column, filepath, start_end_datetime_processed, input_filter_dict)
                        # sub_table_widget.cellDoubleClicked.connect(cell_double_click_lambda)

                        upper_clothing_and_colors = [] # Create empty list to contain searched upper clothing and its corresponding color
                        lower_clothing_and_colors = [] # Create empty list to contain searched lower clothing and its corresponding color
                        for i in items['clothing_and_colors']: # Iterate all the detected clothing and colors
                            if i[0][0] == 'upper_clothing':  # If upper clothing, append the clothing class and corresponding color to upper_clothing_and_colors list
                                colors_str_format = ', '.join(i[0][2])
                                upper_clothing_and_colors.append(f'{i[0][1]}: {colors_str_format}')
                            elif i[0][0] == 'lower_clothing': # Else, to lower_clothing_and_colors list
                                colors_str_format = ', '.join(i[0][2])
                                lower_clothing_and_colors.append(f'{i[0][1]}: {colors_str_format}')

                        upper_clothing_and_colors_to_insert = QTableWidgetItem(', '.join(list(set(upper_clothing_and_colors)))) # Join all upper clothing and colors searched entries with command and make a QTableWidget item from it
                        sub_table_widget.setItem(idx, 2, upper_clothing_and_colors_to_insert) # Insert upper clothing and colors QTableWidget item to the third column of sub QTableWidget
                        lower_clothing_and_colors_to_insert = QTableWidgetItem(', '.join(list(set(lower_clothing_and_colors)))) # Join all lower clothing and colors searched entries with command and make a QTableWidget item from it
                        sub_table_widget.setItem(idx, 3, lower_clothing_and_colors_to_insert) # Insert lower clothing and colors QTableWidget item to the third column of sub QTableWidget

                        # print('\n\n\n')
                        # print(timestamp, weapons_in_current_timestamp, upper_clothing_and_colors, lower_clothing_and_colors)

                    sub_table_widget.horizontalHeader().setStretchLastSection(True) # Stretch last column of sub QTableWidget
                    sub_table_widget.verticalHeader().setStretchLastSection(True) # Stretch last row of sub QTableWidget
                    sub_table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                    sub_table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                    sub_table_widget.verticalHeader().hide() # Hide sub QTableWidget row header
                    sub_table_widget.horizontalHeader().hide() # Hide sub QTableWidget column header 
                    sub_table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                    sub_table_widget.setColumnWidth(1, 150)
                    sub_table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
                    sub_table_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

                    sub_table_widget.cellDoubleClicked.connect(cell_double_click_lambda) # Add the lambda function so that when a cell is double clicked, there is a built-in function that will be executed. 
                    self.tableWidget.setCellWidget(row, 1, sub_table_widget) # Finally, insert the sub QTableWidget to the second column. Do this for suceeding rows

                    row += 1 # Add 1 to insert a new row and iterate to it

                    self.tableWidget.horizontalHeader().setStretchLastSection(True) # Stretch last column of main QTableWidget
                    # self.tableWidget.resizeColumnsToContents() # Resize column to contents
                    self.tableWidget.resizeRowsToContents() # Resize rows to contents
                    # self.tableWidget.resizeRowToContents(0)
                    self.tableWidget.resizeColumnToContents(0)
                    
                    self.resultsFrame.setVisible(True)
                    self.emptyDetsPlaceholder.setVisible(False)

                    self.detectionProcessStart_invisible.setVisible(False)
                    self.upperbox_current_index_changed(self.upperbox.currentIndex())
                    self.lowerbox_current_index_changed(self.lowerbox.currentIndex())
            
                else:
                    self.resultsFrame.setVisible(False)
                    self.emptyDetsPlaceholder.setVisible(True)
                    self.emptyDetsLbl.setText("No weapons/clothings detected")

                    self.detectionProcessStart_invisible.setVisible(False)
                    self.upperbox_current_index_changed(self.upperbox.currentIndex())
                    self.lowerbox_current_index_changed(self.lowerbox.currentIndex())
            
            self.populate_history_table()
            self.update_display_num_of_recent_detections()
    
    # Updates Progress Bar
    def updateProgressBar(self, value):
        self.progressBar.setValue(value)

    # Hide and unhides Start Button and Progress Bar
    def hideUnhideStartButtonAndProgressBar(self, show_start=True):
        self.startbutton.setVisible(show_start)
        self.progressBar.setVisible(not(show_start))
        self.cancelbutton.setVisible(not(show_start))
    
    # Disables input widgets
    def disableEnableDetectionButtons(self, enabled=True):
        self.startDateTime.setEnabled(enabled)
        self.endDateTime.setEnabled(enabled)
        self.WeaponBox.setEnabled(enabled)
        self.upperbox.setEnabled(enabled)
        self.lowerbox.setEnabled(enabled)
        self.upcolorbox.setEnabled(enabled)
        self.lowercolorbox.setEnabled(enabled)
        self.selectArchivePathButton.setEnabled(enabled)
        self.startbutton.setEnabled(enabled)

        # To selectively disable upcolorbox and lowercolorbox even if enabled=True
        # We need to disable those two if there are no selected in upperbox and lowerbox
        if enabled == True:
            self.upperbox_current_index_changed(self.upperbox.currentIndex())
            self.lowerbox_current_index_changed(self.lowerbox.currentIndex())
            

class updateacctpass(QMainWindow, Ui_updatesettings):
    def __init__(self, get_userame, updatedfirstname, updatedlastname, updatedemail, getusername,  get_username):
        super().__init__()
        self.ui=Ui_MainWindow()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        reveal_acctset= self.newpassreveal
        reveal_acctset.mouseReleaseEvent = self.toggle_regpass_visibility

        self.updatepassgetusername = get_userame
        self.newfirstconf = updatedfirstname
        self.newlastconf = updatedlastname
        self.newemailconf = updatedemail
        self.dashusername = getusername
        self.loginusername = get_username
        self.updateactsetpass.setAlignment(Qt.AlignmentFlag.AlignCenter)

        confirmsetpassbtn = self.confirmsetpass
        confirmsetpassbtn.clicked.connect(self.updatesettingsconfirm)

        cancelsetpassbtn = self.updatepasscancel
        cancelsetpassbtn.clicked.connect(self.updatesettingscancel)

    def updatesettingsconfirm(self):
        confirmactpass = self.updateactsetpass.text()
        cursor.execute("SELECT * FROM user_login_info WHERE user_regname=? and user_password=?",  (self.updatepassgetusername, confirmactpass))
        check_acctpass = cursor.fetchall()

        if check_acctpass:
            if self.newfirstconf:
                cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.updatepassgetusername,))
                list_newfirstname = cursor.fetchall()

                if list_newfirstname:
                    cursor.execute("UPDATE user_login_info SET user_firstname=? WHERE user_regname=?", (self.newfirstconf, self.updatepassgetusername))
                    db.commit()

                    with lock:
                        logname = self.loginusername
                        activity = "Successfully changed user's first name."
                        logstatus = "SUCCESS"
                        log_activity(logname, activity, logstatus)
                        self.open_successwindow_ui = Success_saved(self.loginusername)
                        self.close()
                        self.open_successwindow_ui.show()

            if self.newlastconf:
                cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.updatepassgetusername,))
                list_newlastname = cursor.fetchall()

                if list_newlastname:
                    cursor.execute("UPDATE user_login_info SET user_lastname=? WHERE user_regname=?", (self.newlastconf, self.updatepassgetusername))
                    db.commit()

                    with lock:
                        logname = self.loginusername
                        activity = "Successfully changed user's last name."
                        logstatus = "SUCCESS"
                        log_activity(logname, activity, logstatus)
                        self.open_successwindow_ui = Success_saved(self.loginusername)
                        self.close()
                        self.open_successwindow_ui.show()

            if self.newemailconf:
                cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.updatepassgetusername,))
                list_newemailname = cursor.fetchall()

                if list_newemailname:
                    cursor.execute("UPDATE user_login_info SET user_email=? WHERE user_regname=?", (self.newemailconf, self.updatepassgetusername))
                    db.commit()

                    with lock:
                        logname = self.loginusername
                        activity = "Successfully changed user's email address."
                        logstatus = "SUCCESS"
                        log_activity(logname, activity, logstatus)
                        self.open_successwindow_ui = Success_saved(self.loginusername)
                        self.close()
                        self.open_successwindow_ui.show()

            if self.dashusername:
                cursor.execute("SELECT * FROM user_login_info WHERE user_regname=?", (self.updatepassgetusername,))
                list_newusername = cursor.fetchall()
                with lock:
                    with open(json_file_path, 'r') as file:
                        userdata = json.load(file)
                    userdata[self.dashusername] = userdata.pop(self.updatepassgetusername)
                    updated_json = json.dumps(userdata, indent=4)
                    with open(json_file_path, 'w') as file:
                        file.write(updated_json)

                    history_path = r'temp_output/table_data.json'
                    if os.path.exists(history_path):  # Check if the file exists
                        try:
                            with open(history_path, 'r') as jsonhis_file:
                                existing_hisdata = json.load(jsonhis_file)

                            update_his = "@" + self.dashusername
                            later_his = "@" + self.updatepassgetusername

                            if later_his in existing_hisdata:
                                # Rename the key and update the JSON data
                                existing_hisdata[update_his] = existing_hisdata.pop(later_his)
                                updated_hisjson = json.dumps(existing_hisdata, indent=4)

                                with open(history_path, 'w') as jsonhis_file:
                                    jsonhis_file.write(updated_hisjson)
                            else:
                                print(f"'{later_his}' is not present in the JSON data.")
                        except FileNotFoundError:
                            print(f"File '{history_path}' not found.")
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON: {e}")
                    else:
                        print(f"No history_path provided.")
                
                
                if os.path.exists(USER_APP_SETTING_PATH):  # Check if the file exists
                    try:
                        with open(USER_APP_SETTING_PATH, 'r') as jsonset_file:
                            existing_appsetdata = json.load(jsonset_file)  # Load JSON data

                            update_set = self.dashusername
                            later_set = self.updatepassgetusername

                            if later_set in existing_appsetdata:
                                existing_appsetdata[update_set] = existing_appsetdata.pop(later_set)
                                updated_settingjson = json.dumps(existing_appsetdata, indent=4)

                                with open(USER_APP_SETTING_PATH, 'w') as jsonset_file:
                                    jsonset_file.write(updated_settingjson)
                            else:
                                print(f"'{update_set}' is not present in the CONFIG data.")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                else:
                    print(f"File '{USER_APP_SETTING_PATH}' not found.")

                if list_newusername:
                    cursor.execute("UPDATE user_login_info SET user_regname=? WHERE user_regname=?", (self.dashusername, self.updatepassgetusername))
                    db.commit()

                    with lock:
                        logname = self.dashusername
                        activity = "Successfully changed user's username."
                        logstatus = "SUCCESS"
                        log_activity(logname, activity, logstatus)
                        self.open_successwindow_ui = Success_saved(self.dashusername)
                        self.close()
                        self.open_successwindow_ui.show()
        else:
            self.open_invlogin_ui = Invalid_acct_pass()
            self.open_invlogin_ui.show()

    def updatesettingscancel(self):
        self.close()
        
    def toggle_regpass_visibility(self,event):
        if self.updateactsetpass.echoMode()==QLineEdit.EchoMode.Password:
            self.updateactsetpass.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.updateactsetpass.setEchoMode(QLineEdit.EchoMode.Password)

class change_pass(QMainWindow, Ui_ChangePassWindow):
    def __init__(self, login_username):
        super().__init__()
        self.ui=Ui_MainWindow()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.usernameconf = login_username

        submit_changepass = self.changepassset
        submit_changepass.clicked.connect(self.change_password)

        cancel_changepass = self.changepasscancel
        cancel_changepass.clicked.connect(self.change_passwordcancel)

        reveal_oldpasssetbtn = self.revealoldpass
        reveal_oldpasssetbtn.mouseReleaseEvent = self.toggle_regpass1_visibility
        reveal_newpasssetbtn = self.newpasssetreveal
        reveal_newpasssetbtn.mouseReleaseEvent = self.toggle_regpass2_visibility
        reveal_newconfsetbtn = self.confpasssetreveal
        reveal_newconfsetbtn.mouseReleaseEvent = self.toggle_regpassconf_visibility
    
    def change_password(self):
        getoldpass = self.oldpassset.text()
        getnewpass = self.newpassset.text()
        getnewconfpass = self.confirm_newsetpass.text()
        password_length = len(self.newpassset.text())

        if (password_length < 8 or
            not any(char.isupper() for char in getnewpass) or
            not re.search(r"[!@#$%^&*()\-_=+{};:,<.>]", getnewpass) or
            not any(char.isdigit() for char in getnewpass)):

            self.open_invalid_values_length_ui = Invalid_password_length()
            self.open_invalid_values_length_ui.show()
        else:
            cursor.execute("SELECT * FROM user_login_info WHERE user_regname=? and user_password=?", (self.usernameconf,getoldpass,))
            check_changepass = cursor.fetchall()

            if check_changepass:
                if getnewpass:
                    if getnewpass == getnewconfpass:
                        cursor.execute('UPDATE user_login_info SET user_password=? WHERE user_regname=?', (getnewpass, self.usernameconf,))
                        db.commit()

                        with lock:
                            logname = self.usernameconf
                            activity = "Successfully changed the current password."
                            logstatus = "SUCCESS"
                            log_activity(logname, activity, logstatus)
                            self.open_successreset_ui = changepass_success(self.usernameconf)
                            self.open_successreset_ui.show()

                    else:
                        logname = self.usernameconf
                        activity = "Unsuccessful attempt to change current password."
                        logstatus = "FAILED"
                        log_activity(logname, activity, logstatus)
                        self.open_failedreset_ui = Reset_conf_pass()
                        self.open_failedreset_ui.show()
                else:
                    self.open_failedblankpass_ui = add_new_pass()
                    self.open_failedblankpass_ui.show()

            else:
                logname = self.usernameconf
                activity = "Unsuccessful attempt to change current password."
                logstatus = "FAILED"
                log_activity(logname, activity, logstatus)
                self.open_invlogin_ui = Invalid_oldpass()
                self.open_invlogin_ui.show()

    def change_passwordcancel(self):
        self.close()

    def toggle_regpass1_visibility(self,event):
        if self.oldpassset.echoMode()==QLineEdit.EchoMode.Password:
            self.oldpassset.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.oldpassset.setEchoMode(QLineEdit.EchoMode.Password)

    def toggle_regpass2_visibility(self,event):
        if self.newpassset.echoMode()==QLineEdit.EchoMode.Password:
            self.newpassset.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.newpassset.setEchoMode(QLineEdit.EchoMode.Password)

    def toggle_regpassconf_visibility(self,event):
        if self.confirm_newsetpass.echoMode()==QLineEdit.EchoMode.Password:
            self.confirm_newsetpass.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.confirm_newsetpass.setEchoMode(QLineEdit.EchoMode.Password)

######################## Customs pop-up notifications ##########################

##Pop-up for top expired
class OTPexpired(QMainWindow, Ui_expiredotp):
    def __init__(self):
        super().__init__()
        self.ui=Ui_expiredotp()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#expiredotp { border: 1px solid black;}")
        ok_btn = self.ok_otpexpired
        ok_btn.clicked.connect(self.ok_clicked)

    def ok_clicked(self):
        self.close()

##Pop-up for success account settings change
class Success_saved(QMainWindow, Ui_success_win):
    def __init__(self, loginusername):
        super().__init__()
        self.ui=Ui_success_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#success_win { border: 1px solid black;}")
        self.currentuserlogged = loginusername
        current_success_text =  self.tofillupsuccess
        current_success_text.setText(' Account Settings Updated!\n\n Changes have been saved.')
        success_btn = self.ok_backlogin
        success_btn.clicked.connect(self.ok_success_clicked)

    def ok_success_clicked(self):
        all_windows = QApplication.topLevelWidgets()
        for window in all_windows:
            if window is not self:
                window.close()
            else:
                self.open_main_ui = AppWindow(self.currentuserlogged)
                self.open_main_ui.show()
                self.close()

##Pop-up for success registration
class Success_Reg(QMainWindow, Ui_success_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_success_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#success_win { border: 1px solid black;}")
        current_success_text =  self.tofillupsuccess
        current_success_text.setText(' Registration Complete!\n\n Welcome!, You can now login.')
        success_btn = self.ok_backlogin
        success_btn.clicked.connect(self.ok_success_clicked)

    def ok_success_clicked(self):
        all_windows = QApplication.topLevelWidgets()
        self.open_app_ui = AppWindow(0)
        for window in all_windows:
            if not isinstance(window, LoginWindow):
                window.close()
            else:
                self.close()

##Pop-up for success application setting
class Success_appset(QMainWindow, Ui_success_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_success_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#success_win { border: 1px solid black;}")
        current_success_text =  self.tofillupsuccess
        current_success_text.setText(' Action Complete!\n\n Application settings have been saved')
        success_btn = self.ok_backlogin
        success_btn.clicked.connect(self.ok_success_clicked)

    def ok_success_clicked(self):
        self.close()

class failed_exportpath(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Selecting export path failed.\n\n Cancel button has been pressed.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()


##Pop-up for invalid otp in registration
class Failed_reg(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText('  Registration Incomplete!\n\n  Please enter a valid One-time Password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid otp in registration
class Failed_history(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Please enter a numerical value 1-99 \n for your History of Detections to Save.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid email  address in registration
class Invalid_reg_email(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to register!\n\n Please enter a valid email address.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid blank user fullname in registration
class Invalid_reg_blankuserfullname(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to register!\n\n Please enter your full name.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid blank username in registration
class Invalid_reg_blankusern(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to register!\n\n Please enter a valid username.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid blank reg in registration
class Invalid_reg_blankreg(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to register!\n\n Please fill out the registration form.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid blank password in registration
class Invalid_reg_blankpass(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to register!\n\n Please enter a valid password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for password not match in registration
class Invalid_conf_pass(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to Register\n\n Password do not matched.\n Please enter a matched password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for taken email in registration
class Invalid_taken_email(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to Register\n\n Email address is already taken.\n Please try another email address.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for taken username in registration
class Invalid_taken_username(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to Register\n\n Username already taken.\n Please try another username.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid login
class Invalid_oldpass(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to change password\n\n Please enter your correct old password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid login
class Invalid_login(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to Login\n\n Please enter a valid credentials.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid password account settings
class Invalid_acct_pass(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to save changes\n\n Please enter a valid password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()


##Pop-up for invalid password account settings
class DetectionProcessFailDialogBox_NeedAtLeastOne(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText('Detection process failed. \nPlease choose at least a weapon, \nlower clothing, and upper clothing.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class DetectionProcessSuccess_NoDetections(QMainWindow, Ui_success_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_success_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#success_win { border: 1px solid black; }")
        current_success_text =  self.tofillupsuccess
        current_success_text.setText('Process finished but no detections found.\nNo results saved.')
        success_btn = self.ok_backlogin
        success_btn.clicked.connect(self.ok_backvideo)

    def ok_backvideo(self):
        self.close()


##Pop-up for user logout
class user_logout(QMainWindow, Ui_logout_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_logout_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#logout_win { border: 1px solid black; }")
        yesbtn = self.yes_logout
        yesbtn.clicked.connect(self.logout_user)
        cancelbtn = self.cancel_logout
        cancelbtn.clicked.connect(self.cancel_logout_user)

    def logout_user(self):
        all_windows = QApplication.topLevelWidgets()
        self.open_app_ui = AppWindow(0)
        for window in all_windows:
            if window is not self and self.open_app_ui:
                window.close()
            else:
                self.open_login_ui = LoginWindow()
                self.open_login_ui.show()
                self.close()

    def cancel_logout_user(self):
        self.close()


##Pop-up for unregistered email in password reset
class Unregistered_email_reset(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to reset your password.\n\n Email does not exist.\n Please enter a registered email.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid email in password reset
class Invalid_email_reset(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText('Unable to reset your password.\n\n Please enter a valid email address.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid email and username in account settings update
class Invalid_username_email(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText('Unable to update your changes.\n\n Please enter a valid and unregistered \n username and email address.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class Invalid_username_length(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Please enter a valid username \n with atleast 5 characters long.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class Invalid_values_length(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Unable to save your changes. \n Please input a new details.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class Invalid_email_length(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Please enter a valid email address \n with atleast 10 characters long.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class Invalid_firstname_length(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Please enter a valid firstname \n with atleast 2 characters long.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class Invalid_lastname_length(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Please enter a valid lastname \n with atleast 2 characters long.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class Invalid_password_length(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Please enter a valid password \n with at least 8 characters long and \n has 1 uppercase letter, 1 number, \n and 1 special character.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid email in account settings update
class Invalid_email_update(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText('Unable to update your email.\n\n Please enter a valid email or \n unregistered email address.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

## Pop-up for invalid username in account settings update
class Invalid_username_update(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText('Unable to update your username.\n\n Please enter a valid username \n or unregistered username.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

##Pop-up for invalid otp in password reset
class Failed_reset(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText('  Unable to reset your password.\n\n  Please enter a valid One-time Password')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class add_new_pass(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Action failed.\n\n Please enter a new password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class Reset_conf_pass(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Action failed.\n\n Password do not matched.\n Please enter a matched password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()


class No_video_detect(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        failed_detection_txt =  self.tofillupfailed
        failed_detection_txt.setText(' No available videos to process. \n Filter detection process failed.')
        failed_btn = self.ok_failedbtn
        failed_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()


class Reset_blank_pass(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Action failed.\n\n Please enter a valid password.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class deleted_saved(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black; }")
        current_success_text =  self.tofillupfailed
        current_success_text.setText(' Failed to open the saved video.\n\n It seems like the file has been deleted \n or has been moved to another folder.')
        success_btn = self.ok_failedbtn
        success_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()
    

class Reset_success(QMainWindow, Ui_success_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_success_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#success_win { border: 1px solid black;}")
        current_success_text =  self.tofillupsuccess
        current_success_text.setText(' Password reset complete.\n\n Successfully updated your password.')
        success_btn = self.ok_backlogin
        success_btn.clicked.connect(self.ok_success_clicked)

    def ok_success_clicked(self):
        all_windows = QApplication.topLevelWidgets()
        for window in all_windows:
            if window is not self:
                window.close()
            else:
                self.open_login_ui = LoginWindow()
                self.open_login_ui.show()
                self.close()

class warning_range(QMainWindow, Ui_alert_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_alert_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#alert_win { border: 1px solid black;}")
        no_btn = self.ok_proceed
        no_btn.clicked.connect(self.ok_clicked)

    def ok_clicked(self):
        self.close()

class invalid_dateparam(QMainWindow, Ui_failed_win):
    def __init__(self):
        super().__init__()
        self.ui=Ui_failed_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#failed_win { border: 1px solid black;}")
        failed_detection_txt =  self.tofillupfailed
        failed_detection_txt.setText('\n Invalid input for date range.\n Please try again with valid date.')
        failed_btn = self.ok_failedbtn
        failed_btn.clicked.connect(self.ok_failed_clicked)

    def ok_failed_clicked(self):
        self.close()

class invalid_param(QMainWindow, Ui_param_win):
    def __init__(self, invalidvars):
        super().__init__()
        self.ui=Ui_param_win()
        self.setupUi(self)
        invalidvariables = invalidvars

        if "Invalid/Non-existing archive path" in invalidvariables:
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
            self.setStyleSheet("#param_win { border: 1px solid black;}")
            failed_detection_txt =  self.tofillupsuccess
            failed_detection_txt.setText(' {} \n\n Please select the appropriate archive folder.'.format(invalidvariables[0], "\n".join("\t\u2b29 {}".format(var) for var in invalidvariables[1:])))
            failed_btn = self.no_proceed
            failed_btn.clicked.connect(self.ok_failed_clicked)
        else:
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
            self.setStyleSheet("#param_win { border: 1px solid black; }")
            failed_detection_txt =  self.tofillupsuccess
            failed_detection_txt.setText('\n\nChoose an appropriate category for the\nfollowing:\n{}'.format("\n".join("\t\u2b29 {}".format(var) for var in invalidvariables)))
            failed_btn = self.no_proceed
            failed_btn.clicked.connect(self.ok_failed_clicked)
 
    def ok_failed_clicked(self):
        self.close()

class changepass_success(QMainWindow, Ui_success_win):
    def __init__(self, usernameconf):
        super().__init__()
        self.ui=Ui_success_win()
        self.setupUi(self)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("#success_win { border: 1px solid black; }")
        current_success_text =  self.tofillupsuccess
        self.currentuserlogged = usernameconf
        current_success_text.setText(' Password change complete.\n\n Successfully updated your password.')
        success_btn = self.ok_backlogin
        success_btn.clicked.connect(self.ok_success_clicked)

    def ok_success_clicked(self):
        all_windows = QApplication.topLevelWidgets()
        for window in all_windows:
            if window is not self:
                window.close()
            else:
                self.open_login_ui = AppWindow(self.currentuserlogged)
                self.open_login_ui.show()
                self.close()

if __name__== '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())