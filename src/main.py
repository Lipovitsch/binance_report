################### Program Info ###################
VERSION = "1.0"
RELEASE = "2023/11/19 16:00"
INFO_GUI = f"""
VERSION
{VERSION}

RELEASE
{RELEASE}

AUTHOR
Norbert Lipowicz
"""
MAIN_WINDOW = "Binance Report Generator v" + VERSION
####################################################


import os
import sys
import traceback
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDateEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *

from exceptions import *
from excel_writer import ExcelWriter
from gui import Ui_MainWindow
from binance_report import BinanceReport, get_api_keys


def show_msgbox(message: str, msg_type: str, **kwargs):
    """Types: Information, Warning, Error"""
    msg = QMessageBox()
    # msg.setWindowIcon(get_icon())
    if msg_type == "Information":
        msg.setIcon(QMessageBox.Information)

        if "open_folder" in kwargs.keys():
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
            msg.button(QMessageBox.Open).setText(kwargs["open_folder"])

    elif msg_type == "Warning":
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No, "Test")

    elif msg_type == "Error":
        msg.setIcon(QMessageBox.Critical)

    msg.setWindowTitle(msg_type)
    msg.setText(message)
    return msg.exec_()


def browse_save_file(current, caption, filter):
    path = QFileDialog.getSaveFileName(
        caption=caption,
        filter=filter
    )[0]
    return path if path != "" else current


def browse_open_file(current, caption, filter):
    path = QFileDialog.getOpenFileName(
        caption = caption, 
        filter = filter
    )[0]
    return path if path != "" else current


def get_date_as_datetime(date_attr: QDateEdit):
    date = date_attr.text().split('.')
    date = [int(el) for el in date]
    return datetime(year=date[2], month=date[1], day=date[0])


class ThreadSignals(QObject):
    set_gui_state = pyqtSignal(bool)
    finished = pyqtSignal()
    error = pyqtSignal(Exception)
    progress = pyqtSignal(str)


class Thread(QThread):
    def __init__(self, fn, *args, **kwargs):
        super(Thread, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = ThreadSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.signals.set_gui_state.emit(False)
            self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit(e)

        finally:
            self.signals.set_gui_state.emit(True)


class BRMainWindow(Ui_MainWindow):
    def __init__(self):
        # class variables definition
        self.path_api_keys = ''
        self.path_report = ''

        self.MainWindow = QtWidgets.QMainWindow()
        self.setupUi(self.MainWindow)
        self.MainWindow.setWindowTitle(MAIN_WINDOW)

        self.GUI_MenuBar_Info.triggered.connect(self.show_program_info)
        self.GUI_Button_KluczeAPI.clicked.connect(self.browse_path_api_keys)
        self.Gui_Button_LokalizacjaRaportu.clicked.connect(self.browse_path_report)
        self.GUI_MenuBar_Generuj.triggered.connect(self.generate_template_api_keys)
        self.GUI_Button_GenerujRaport.clicked.connect(self.run_program)

        app.aboutToQuit.connect(self.end_program)


    def show_program_info(self):
        show_msgbox(INFO_GUI, "Information")
    

    def browse_path_api_keys(self):
        self.path_api_keys = browse_open_file(
                current = self.path_api_keys,
                caption = "Wyszukaj plik kluczy API",
                filter = "Pliki JSON (*.json)"
            )
        self.GUI_LineEdit_KluczeAPI.setText(self.path_api_keys)
    

    def browse_path_report(self):
        self.path_report = browse_save_file(
                current = self.path_report,
                caption = "Wyszukaj lokalizację raportu",
                filter = "Pliki Excel (*.xlsx)"
            )
        self.GUI_LineEdit_LokalizacjaRaportu.setText(self.path_report)
    

    def generate_template_api_keys(self):
        path = ''
        path = browse_save_file(
            current = path,
            caption = "Wyszukaj lokalizację dla szablonu pliku kluczy API",
            filter = "Pliki JSON (*.json)"
            )
        if path != '':
            with open(path, 'w') as f:
                f.write("""{\n\t"api_key": "xxxxxxxxxx",\n\t"secret_key": "xxxxxxxxxx"\n}""")
            result = show_msgbox("Zapisano szablon pliku kluczy API", "Information", open_folder = "Otwórz plik")
            if result == QMessageBox.Open:
                os.startfile(path)


    def generate_report(self, progress_callback = None):
        start_date = get_date_as_datetime(self.GUI_Date_Start)
        end_date = get_date_as_datetime(self.GUI_Date_End)
        
        if end_date <= start_date:
            raise DateError("Błędny zakres dat")

        if self.path_api_keys == '':
            raise PathError("Podaj lokalizację pliku kluczy API")
        
        if self.path_report == '':
            raise PathError("Podaj lokalizację do zapisu raportu")
        
        api_key, secret_key = get_api_keys(self.path_api_keys)

        binance_report = BinanceReport(api_key=api_key, secret_key=secret_key, progress_callback=progress_callback)

        output_df_dict = {}
        list_of_empty = []

        if self.GUI_CheckBox_Krypto.isChecked():
            output_df_dict["Krypto"] = binance_report.get_crypto_transactions(start_date, end_date)
            if len(output_df_dict["Krypto"]) == 0:
                list_of_empty.append("Krypto")
        
        if self.GUI_CheckBox_P2P.isChecked():
            output_df_dict["P2P"] = binance_report.get_p2p_transactions(start_date, end_date)
            if len(output_df_dict["P2P"]) == 0:
                list_of_empty.append("P2P")
        
        if self.GUI_CheckBox_FIAT.isChecked():
            output_df_dict["FIAT"] = binance_report.get_fiat_transactions(start_date, end_date)
            if len(output_df_dict["FIAT"]) == 0:
                list_of_empty.append("FIAT")
        
        if len(list_of_empty) > 0:
            add_info = ''
            if len(list_of_empty) == len(output_df_dict.keys()):
                add_info = "\nNie wygenerowano raportu."
            show_msgbox(f"Nie znaleziono transakcji dla: {', '.join(list_of_empty)}.{add_info}", msg_type="Information")
        
        updated_output_df_dict = {}
        for key in output_df_dict.keys():
            if key not in list_of_empty:
                updated_output_df_dict[key] = output_df_dict[key]

        if len(updated_output_df_dict) > 0:
            xlsx_writer = ExcelWriter(self.path_report)
            xlsx_writer.save_dataframes_to_excel(updated_output_df_dict)
        else:
            raise CheckBoxError("Żaden checkbox nie został zaznaczony")


    # Functions for multithreading
    def program_set_gui_state(self, state: bool):
        self.menuPlik.setEnabled(state)
        self.GUI_GroupBox_KluczeAPI.setEnabled(state)
        self.GUI_GroupBox_Wybor.setEnabled(state)
        self.GUI_GroupBox_Daty.setEnabled(state)
        self.GUI_GroupBox_LokalizacjaRaportu.setEnabled(state)
        self.GUI_Button_GenerujRaport.setEnabled(state)


    def program_finished(self):
        self.GUI_Label_Progress.setText('')
        result = show_msgbox("Wygenerowano raport", "Information", open_folder = "Otwórz plik")
        if result == QMessageBox.Open:
            os.startfile(self.path_report)
    

    def program_error(self, e):
        self.GUI_Label_Progress.setText('')
        if issubclass(type(e), BinanceReportException):
            show_msgbox(f"Rodzaj błędu:\n{type(e).__name__}\n\nOpis błędu:\n{e}", msg_type="Error")
        else:
            err_desc = traceback.format_exception(e)
            show_msgbox(f"Wystąpił nieobsługiwany błąd. Skontaktuj się z autorem.\n\nOpis błędu:\n{''.join(err_desc)}", msg_type="Error")


    def program_update_progress(self, text):
        self.GUI_Label_Progress.setText(text)
    

    def run_program(self):
        self.thread = Thread(self.generate_report)
        self.thread.signals.set_gui_state.connect(self.program_set_gui_state)
        self.thread.signals.progress.connect(self.program_update_progress)
        self.thread.signals.error.connect(self.program_error)
        self.thread.signals.finished.connect(self.program_finished)
        self.thread.start()
    

    def end_program(self):
        if type(self.thread) == Thread:
            self.thread.exit()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = BRMainWindow()
    ui.MainWindow.show()
    sys.exit(app.exec_())