################### Program Info ###################
VERSION = "1.2"
RELEASE = "2023/11/25 13:30"
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
import json
import traceback
from datetime import datetime

import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDateEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
import icon

from exceptions import *
from const import *
from nbp_api import NBPAPI
from excel_writer import ExcelWriter
from gui import Ui_MainWindow
from binance_report import BinanceReport, get_api_keys


def show_msgbox(message: str, msg_type: str, **kwargs):
    """Types: Information, Warning, Error"""
    msg = QMessageBox()
    icon = QIcon(":Logo.png")
    msg.setWindowIcon(icon)
    # msg.setWindowIcon(get_icon())
    if msg_type == "Information":
        msg.setIcon(QMessageBox.Information)

        if "option_open" in kwargs.keys():
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
            msg.button(QMessageBox.Open).setText(kwargs["option_open"])

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
    finished = pyqtSignal(str)
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
            res = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(res)

        except Exception as e:
            self.signals.error.emit(e)

        finally:
            self.signals.set_gui_state.emit(True)


class BRMainWindow(Ui_MainWindow):
    def __init__(self):
        # class variables definition
        self.path_api_keys = ''
        self.path_report = ''
        self.binance_symbols = []
        self.thread: Thread = '' # placeholder

        self.MainWindow = QtWidgets.QMainWindow()
        self.setupUi(self.MainWindow)
        self.MainWindow.setWindowTitle(MAIN_WINDOW)

        icon = QIcon(':Logo.png')
        self.MainWindow.setWindowIcon(icon)

        self.GUI_MenuBar_ProgramInfo.triggered.connect(self.show_program_info)
        self.GUI_Button_KluczeAPI.clicked.connect(self.browse_path_api_keys)
        self.Gui_Button_LokalizacjaRaportu.clicked.connect(self.browse_path_report)
        self.GUI_MenuBar_Generuj.triggered.connect(self.generate_template_api_keys)
        self.GUI_Button_GenerujRaport.clicked.connect(self.run_program)
        self.GUI_CheckBox_Krypto.clicked.connect(self.set_crypto_choice_state)
        self.GUI_GroupBox_WyborKrypto.clicked.connect(self.set_crypto_choice_internal_state)
        self.GUI_LineEdit_Symbol.textChanged.connect(self.update_binance_symbols_list)
        self.GUI_List_Symbol.itemDoubleClicked.connect(self.add_chosen_symbol)
        self.GUI_List_SymbolChosen.itemDoubleClicked.connect(self.remove_chosen_symbol)

        app.aboutToQuit.connect(self.end_program)

        # set initial state
        self.GUI_GroupBox_Wybor.setEnabled(False)
        self.GUI_GroupBox_Daty.setEnabled(False)
        self.GUI_GroupBox_Raport.setEnabled(False)

        binance_report = BinanceReport()
        self.binance_symbols = binance_report.get_symbols()
        self.GUI_Label_SymbolList.setText(f"Dostępne symbole ({len(self.binance_symbols)})")
        self.GUI_List_Symbol.clear()
        self.GUI_List_Symbol.addItems(self.binance_symbols)


    def show_program_info(self):
        show_msgbox(INFO_GUI, "Information")
    

    def browse_path_api_keys(self):
        self.path_api_keys = browse_open_file(
                current = self.path_api_keys,
                caption = "Wyszukaj plik kluczy API",
                filter = "Pliki JSON (*.json)"
            )
        self.GUI_LineEdit_KluczeAPI.setText(self.path_api_keys)

        if self.path_api_keys != '':
            self.GUI_GroupBox_Wybor.setEnabled(True)
            self.GUI_GroupBox_Daty.setEnabled(True)
            self.GUI_GroupBox_Raport.setEnabled(True)


    def browse_path_report(self):
        self.path_report = browse_save_file(
                current = self.path_report,
                caption = "Wyszukaj lokalizację raportu",
                filter = "Pliki Excel (*.xlsx)"
            )
        self.GUI_LineEdit_LokalizacjaRaportu.setText(self.path_report)
    

    def set_crypto_choice_state(self):
        krypto_checkbox_state = self.GUI_CheckBox_Krypto.isChecked()
        self.GUI_GroupBox_WyborKrypto.setEnabled(krypto_checkbox_state)

    
    def set_crypto_choice_internal_state(self):
        krypto_choice_groupbox_state = self.GUI_GroupBox_WyborKrypto.isChecked()
        self.GUI_Label_Symbol.setEnabled(krypto_choice_groupbox_state)
        self.GUI_Label_SymbolList.setEnabled(krypto_choice_groupbox_state)
        self.GUI_Label_SymbolChosen.setEnabled(krypto_choice_groupbox_state)
        self.GUI_LineEdit_Symbol.setEnabled(krypto_choice_groupbox_state)
        self.GUI_List_Symbol.setEnabled(krypto_choice_groupbox_state)
        self.GUI_List_SymbolChosen.setEnabled(krypto_choice_groupbox_state)


    def update_binance_symbols_list(self):
        curr_text = self.GUI_LineEdit_Symbol.text().upper()
        symbols = [symbol for symbol in self.binance_symbols if curr_text in symbol]
        self.GUI_List_Symbol.clear()
        self.GUI_List_Symbol.addItems(symbols)


    def add_chosen_symbol(self):
        symbol = self.GUI_List_Symbol.currentItem()
        self.GUI_List_SymbolChosen.addItem(symbol.text())


    def remove_chosen_symbol(self):
        symbol = self.GUI_List_SymbolChosen.currentItem()
        row = self.GUI_List_SymbolChosen.row(symbol)
        self.GUI_List_SymbolChosen.takeItem(row)


    def get_chosen_symbols(self) -> list:
        symbols = self.GUI_List_SymbolChosen.findItems("*", Qt.MatchFlag.MatchWildcard)
        return [symbol.text() for symbol in symbols]

    
    def generate_template_api_keys(self):
        path = ''
        path = browse_save_file(
            current = path,
            caption = "Wyszukaj lokalizację dla szablonu pliku kluczy API",
            filter = "Pliki JSON (*.json)"
            )
        if path != '':
            with open(path, 'w') as f:
                f.write("""{\n\t"api_key": "tutaj_wklej_klucz_publiczny",\n\t"secret_key": "tutaj_wklej_klucz_prywatny"\n}""")
            result = show_msgbox("Zapisano szablon pliku kluczy API", "Information", option_open = "Otwórz plik")
            if result == QMessageBox.Open:
                os.startfile(path)


    def generate_report(self, progress_callback = None):
        start_date = get_date_as_datetime(self.GUI_Date_Start)
        end_date = get_date_as_datetime(self.GUI_Date_End)

        if self.path_api_keys == '':
            raise PathError("Podaj lokalizację pliku kluczy API")
        
        try:
            api_key, secret_key = get_api_keys(self.path_api_keys)
        except json.decoder.JSONDecodeError as e:
            raise APIKeysError(f"Wykryto błąd w składni pliku JSON z kluczami API\n{e}")
        
        if end_date <= start_date:
            raise DateError("Błędny zakres dat")

        if self.path_report == '':
            raise PathError("Podaj lokalizację do zapisu raportu")
        
        chosen_symbols = None
        if self.GUI_GroupBox_WyborKrypto.isChecked() and self.GUI_GroupBox_WyborKrypto.isEnabled():
            chosen_symbols = self.get_chosen_symbols()
            if len(chosen_symbols) == 0:
                raise SymbolsError("Wybierz symbole lub odznacz 'Wybór krypto'")
        
        binance_report = BinanceReport(api_key=api_key, secret_key=secret_key, progress_callback=progress_callback)

        output_df_dict = {}
        list_of_empty = []
        list_of_checked = []

        if self.GUI_CheckBox_Krypto.isChecked():
            list_of_checked.append("Krypto")
            output_df_dict["Krypto"] = binance_report.get_crypto_transactions(start_date, end_date, chosen_symbols)
            if len(output_df_dict["Krypto"]) == 0:
                list_of_empty.append("Krypto")
        
        if self.GUI_CheckBox_P2P.isChecked():
            list_of_checked.append("P2P")
            output_df_dict["P2P"] = binance_report.get_p2p_transactions(start_date, end_date)
            if len(output_df_dict["P2P"]) == 0:
                list_of_empty.append("P2P")
        
        if self.GUI_CheckBox_FIATKrypto.isChecked():
            list_of_checked.append("FIAT_Krypto")
            output_df_dict["FIAT_Krypto"] = binance_report.get_fiat_crypto_transactions(start_date, end_date)
            if len(output_df_dict["FIAT_Krypto"]) == 0:
                list_of_empty.append("FIAT_Krypto")
        
        if self.GUI_CheckBox_FIAT.isChecked():
            list_of_checked.append("FIAT")
            output_df_dict["FIAT"] = binance_report.get_fiat_transactions(start_date, end_date)
            if len(output_df_dict["FIAT"]) == 0:
                list_of_empty.append("FIAT")
        
        if self.GUI_CheckBox_RaportPodatkowy.isChecked():
            list_of_checked.append("Raport_podatkowy")

            p2p_df = binance_report.get_p2p_transactions(start_date, end_date) if not "P2P" in output_df_dict.keys() else output_df_dict["P2P"]
            fiat_krypto_df = binance_report.get_fiat_crypto_transactions(start_date, end_date) if not "FIAT_Krypto" in output_df_dict.keys() else output_df_dict["FIAT_Krypto"]
            fiat_df = binance_report.get_fiat_transactions(start_date, end_date) if not "FIAT" in output_df_dict.keys() else output_df_dict["FIAT"]

            fiat_krypto_df = fiat_krypto_df[fiat_krypto_df["Rodzaj handlu"] == "Wpłata"]

            columns = ["Data utworzenia", "Ilość FIAT", "Prowizja", "FIAT", "Rodzaj handlu"]
            to_concat = [el[columns] for el in [p2p_df, fiat_krypto_df, fiat_df] if len(el) > 0]
            raport_podatkowy_df = pd.concat(to_concat) if len(p2p_df) > 0 or len(fiat_krypto_df) > 0 or len(fiat_df) > 0 else pd.DataFrame()

            if len(raport_podatkowy_df) > 0:
                raport_podatkowy_df.sort_values(by="Data utworzenia", inplace=True)
                raport_podatkowy_df['Ilość FIAT'] = raport_podatkowy_df.apply(lambda x: x['Ilość FIAT'] if x['Rodzaj handlu'] == 'Wpłata' else -1 * x['Ilość FIAT'], axis=1)
                raport_podatkowy_df['Kurs do PLN'] = raport_podatkowy_df.apply(lambda x: 1 if x['FIAT'] == 'PLN' else NBPAPI().get_mid_price(x['FIAT'], x['Data utworzenia']), axis=1)
                raport_podatkowy_df['Wartość końcowa PLN'] = (raport_podatkowy_df['Ilość FIAT'] * raport_podatkowy_df['Kurs do PLN']).round(2)
                raport_podatkowy_df['Koszt(+)/Dochód(-)'] = raport_podatkowy_df['Wartość końcowa PLN'].cumsum().round(2)
            else:
                list_of_empty.append("Raport_podatkowy")
            
            output_df_dict["Raport_podatkowy"] = raport_podatkowy_df
        
        if len(output_df_dict) == 0:
            raise CheckBoxError("Nie wybrano żadnej opcji")
    
        end_msg = ''
        if len(list_of_empty) > 0:
            if len(list_of_empty) == len(output_df_dict.keys()):
                end_msg = Messages.TRANSACTIONS_NOT_FOUND % ', '.join(list_of_empty) + '\n' + Messages.REPORT_NOT_GENERATED
            else:
                end_msg = Messages.TRANSACTIONS_NOT_FOUND % ', '.join(list_of_empty) + '\n' + Messages.REPORT_GENERATED
        
        updated_output_df_dict = {}
        for key in output_df_dict.keys():
            if key not in list_of_empty and key in list_of_checked:
                updated_output_df_dict[key] = output_df_dict[key]

        if len(updated_output_df_dict) > 0:
            xlsx_writer = ExcelWriter(self.path_report)
            xlsx_writer.save_dataframes_to_excel(updated_output_df_dict)
        
        if end_msg == '':
            return Messages.REPORT_GENERATED
        else:
            return end_msg


    # Functions for multithreading
    def program_set_gui_state(self, state: bool):
        self.menuPlik.setEnabled(state)
        self.GUI_GroupBox_API.setEnabled(state)
        self.GUI_GroupBox_Wybor.setEnabled(state)
        self.GUI_GroupBox_Daty.setEnabled(state)
        self.GUI_GroupBox_Raport.setEnabled(state)
        self.GUI_Button_GenerujRaport.setEnabled(state)


    def program_finished(self, res: str | None):
        self.GUI_Label_Progress.setText('')

        if Messages.REPORT_GENERATED in res:
            result = show_msgbox(res, "Information", option_open = "Otwórz plik")
            if result == QMessageBox.Open:
                os.startfile(self.path_report)
        else:
            result = show_msgbox(res, "Information")
    

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