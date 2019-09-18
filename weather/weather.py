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

from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QRunnable, QSize,  Qt, QThreadPool, Signal, Slot)
from PySide2.QtGui import (QFont, QIcon, QPixmap)
from PySide2.QtWidgets import (QApplication, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QVBoxLayout, QWidget)

#from MainWindow import Ui_MainWindow

OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')

"""
Get an API key from https://openweathermap.org/ to use with this
application.

"""


def from_ts_to_time_of_day(ts):
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%I%p").lstrip("0")


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    '''
    finished = Signal()
    
    error = Signal(str)
    result = Signal(dict, dict)

#class QWeather(QMainWindow):
class WeatherWorker(QRunnable):
    '''
    Worker thread for weather updates.
    '''
    signals = WorkerSignals()
    is_interrupted = False

    def __init__(self, location):
        super(WeatherWorker, self).__init__()
        self.location = location

    @Slot(str) 
    def run(self):
        try:
            params = dict(
                q=self.location,
                appid=OPENWEATHERMAP_API_KEY
            )

            url = 'http://api.openweathermap.org/data/2.5/weather?%s&units=metric' % urlencode(params)
            print(url)
            r = requests.get(url)
            weather = json.loads(r.text)

            # Check if we had a failure (the forecast will fail in the same way).
            if weather['cod'] != 200:
                raise Exception(weather['message'])

            url = 'http://api.openweathermap.org/data/2.5/forecast?%s&units=metric' % urlencode(params)
            print(url)
            r = requests.get(url)
            forecast = json.loads(r.text)

            self.signals.result.emit(weather, forecast)

        except Exception as e:
            self.signals.error.emit(str(e))

        self.signals.finished.emit()



class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.pushButton.pressed.connect(self.update_weather)

        self.threadpool = QThreadPool()
        self.update_weather()

        self.show()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(330, 417)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.lineEdit = QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout_3.addWidget(self.lineEdit)
        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setText("")
        icon = QIcon()
        icon.addPixmap(QPixmap("images/arrow-circle-225.png"), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.weatherIcon = QLabel(self.centralwidget)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.weatherIcon.sizePolicy().hasHeightForWidth())
        self.weatherIcon.setSizePolicy(sizePolicy)
        self.weatherIcon.setMinimumSize(QSize(64, 64))
        self.weatherIcon.setMaximumSize(QSize(64, 64))
        self.weatherIcon.setText("")
        self.weatherIcon.setObjectName("weatherIcon")
        self.horizontalLayout_4.addWidget(self.weatherIcon)
        self.weatherLabel = QLabel(self.centralwidget)
        self.weatherLabel.setText("")
        self.weatherLabel.setObjectName("weatherLabel")
        self.horizontalLayout_4.addWidget(self.weatherLabel)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.forecastIcon4 = QLabel(self.centralwidget)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.forecastIcon4.sizePolicy().hasHeightForWidth())
        self.forecastIcon4.setSizePolicy(sizePolicy)
        self.forecastIcon4.setMinimumSize(QSize(64, 64))
        self.forecastIcon4.setMaximumSize(QSize(200, 32))
        self.forecastIcon4.setBaseSize(QSize(0, 0))
        self.forecastIcon4.setText("")
        self.forecastIcon4.setAlignment(Qt.AlignCenter)
        self.forecastIcon4.setObjectName("forecastIcon4")
        self.gridLayout_2.addWidget(self.forecastIcon4, 1, 3, 1, 1)
        self.forecastTemp2 = QLabel(self.centralwidget)
        self.forecastTemp2.setText("")
        self.forecastTemp2.setObjectName("forecastTemp2")
        self.gridLayout_2.addWidget(self.forecastTemp2, 2, 1, 1, 1)
        self.forecastTemp5 = QLabel(self.centralwidget)
        self.forecastTemp5.setText("")
        self.forecastTemp5.setObjectName("forecastTemp5")
        self.gridLayout_2.addWidget(self.forecastTemp5, 2, 4, 1, 1)
        self.forecastTemp4 = QLabel(self.centralwidget)
        self.forecastTemp4.setText("")
        self.forecastTemp4.setObjectName("forecastTemp4")
        self.gridLayout_2.addWidget(self.forecastTemp4, 2, 3, 1, 1)
        self.forecastIcon2 = QLabel(self.centralwidget)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.forecastIcon2.sizePolicy().hasHeightForWidth())
        self.forecastIcon2.setSizePolicy(sizePolicy)
        self.forecastIcon2.setMinimumSize(QSize(64, 64))
        self.forecastIcon2.setMaximumSize(QSize(200, 32))
        self.forecastIcon2.setBaseSize(QSize(0, 0))
        self.forecastIcon2.setText("")
        self.forecastIcon2.setAlignment(Qt.AlignCenter)
        self.forecastIcon2.setObjectName("forecastIcon2")
        self.gridLayout_2.addWidget(self.forecastIcon2, 1, 1, 1, 1)
        self.forecastIcon5 = QLabel(self.centralwidget)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.forecastIcon5.sizePolicy().hasHeightForWidth())
        self.forecastIcon5.setSizePolicy(sizePolicy)
        self.forecastIcon5.setMinimumSize(QSize(64, 64))
        self.forecastIcon5.setMaximumSize(QSize(200, 32))
        self.forecastIcon5.setBaseSize(QSize(0, 0))
        self.forecastIcon5.setText("")
        self.forecastIcon5.setAlignment(Qt.AlignCenter)
        self.forecastIcon5.setObjectName("forecastIcon5")
        self.gridLayout_2.addWidget(self.forecastIcon5, 1, 4, 1, 1)
        self.forecastIcon1 = QLabel(self.centralwidget)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.forecastIcon1.sizePolicy().hasHeightForWidth())
        self.forecastIcon1.setSizePolicy(sizePolicy)
        self.forecastIcon1.setMinimumSize(QSize(64, 64))
        self.forecastIcon1.setMaximumSize(QSize(200, 32))
        self.forecastIcon1.setBaseSize(QSize(0, 0))
        self.forecastIcon1.setText("")
        self.forecastIcon1.setAlignment(Qt.AlignCenter)
        self.forecastIcon1.setObjectName("forecastIcon1")
        self.gridLayout_2.addWidget(self.forecastIcon1, 1, 0, 1, 1)
        self.forecastIcon3 = QLabel(self.centralwidget)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.forecastIcon3.sizePolicy().hasHeightForWidth())
        self.forecastIcon3.setSizePolicy(sizePolicy)
        self.forecastIcon3.setMinimumSize(QSize(64, 64))
        self.forecastIcon3.setMaximumSize(QSize(200, 32))
        self.forecastIcon3.setBaseSize(QSize(0, 0))
        self.forecastIcon3.setText("")
        self.forecastIcon3.setAlignment(Qt.AlignCenter)
        self.forecastIcon3.setObjectName("forecastIcon3")
        self.gridLayout_2.addWidget(self.forecastIcon3, 1, 2, 1, 1)
        self.forecastTemp3 = QLabel(self.centralwidget)
        self.forecastTemp3.setText("")
        self.forecastTemp3.setObjectName("forecastTemp3")
        self.gridLayout_2.addWidget(self.forecastTemp3, 2, 2, 1, 1)
        self.forecastTemp1 = QLabel(self.centralwidget)
        self.forecastTemp1.setText("")
        self.forecastTemp1.setObjectName("forecastTemp1")
        self.gridLayout_2.addWidget(self.forecastTemp1, 2, 0, 1, 1)
        self.forecastTime1 = QLabel(self.centralwidget)
        self.forecastTime1.setAlignment(Qt.AlignCenter)
        self.forecastTime1.setObjectName("forecastTime1")
        self.gridLayout_2.addWidget(self.forecastTime1, 0, 0, 1, 1)
        self.forecastTime2 = QLabel(self.centralwidget)
        self.forecastTime2.setAlignment(Qt.AlignCenter)
        self.forecastTime2.setObjectName("forecastTime2")
        self.gridLayout_2.addWidget(self.forecastTime2, 0, 1, 1, 1)
        self.forecastTime3 = QLabel(self.centralwidget)
        self.forecastTime3.setAlignment(Qt.AlignCenter)
        self.forecastTime3.setObjectName("forecastTime3")
        self.gridLayout_2.addWidget(self.forecastTime3, 0, 2, 1, 1)
        self.forecastTime4 = QLabel(self.centralwidget)
        self.forecastTime4.setAlignment(Qt.AlignCenter)
        self.forecastTime4.setObjectName("forecastTime4")
        self.gridLayout_2.addWidget(self.forecastTime4, 0, 3, 1, 1)
        self.forecastTime5 = QLabel(self.centralwidget)
        self.forecastTime5.setAlignment(Qt.AlignCenter)
        self.forecastTime5.setObjectName("forecastTime5")
        self.gridLayout_2.addWidget(self.forecastTime5, 0, 4, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_2)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_5 = QLabel(self.centralwidget)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_5)
        self.label_6 = QLabel(self.centralwidget)
        self.label_6.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_6)
        self.temperatureLabel = QLabel(self.centralwidget)
        self.temperatureLabel.setText("")
        self.temperatureLabel.setObjectName("temperatureLabel")
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.temperatureLabel)
        self.label_7 = QLabel(self.centralwidget)
        self.label_7.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.label_7)
        self.humidityLabel = QLabel(self.centralwidget)
        self.humidityLabel.setText("")
        self.humidityLabel.setObjectName("humidityLabel")
        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.humidityLabel)
        self.label_8 = QLabel(self.centralwidget)
        self.label_8.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_8)
        self.pressureLabel = QLabel(self.centralwidget)
        self.pressureLabel.setText("")
        self.pressureLabel.setObjectName("pressureLabel")
        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.pressureLabel)
        self.label = QLabel(self.centralwidget)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label)
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.label_2)
        self.longitudeLabel = QLabel(self.centralwidget)
        self.longitudeLabel.setText("")
        self.longitudeLabel.setObjectName("longitudeLabel")
        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.longitudeLabel)
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(8, QFormLayout.LabelRole, self.label_3)
        self.latitudeLabel = QLabel(self.centralwidget)
        self.latitudeLabel.setText("")
        self.latitudeLabel.setObjectName("latitudeLabel")
        self.formLayout.setWidget(8, QFormLayout.FieldRole, self.latitudeLabel)
        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(9, QFormLayout.LabelRole, self.label_4)
        self.sunriseLabel = QLabel(self.centralwidget)
        self.sunriseLabel.setText("")
        self.sunriseLabel.setObjectName("sunriseLabel")
        self.formLayout.setWidget(9, QFormLayout.FieldRole, self.sunriseLabel)
        self.label_9 = QLabel(self.centralwidget)
        self.label_9.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_9.setObjectName("label_9")
        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_9)
        self.label_10 = QLabel(self.centralwidget)
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_10.setFont(font)
        self.label_10.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label_10.setObjectName("label_10")
        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_10)
        self.windLabel = QLabel(self.centralwidget)
        self.windLabel.setText("")
        self.windLabel.setObjectName("windLabel")
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.windLabel)
        self.label_11 = QLabel(self.centralwidget)
        self.label_11.setText("")
        self.label_11.setObjectName("label_11")
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.label_11)
        self.label_13 = QLabel(self.centralwidget)
        self.label_13.setText("")
        self.label_13.setObjectName("label_13")
        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.label_13)
        self.label_12 = QLabel(self.centralwidget)
        self.label_12.setText("")
        self.label_12.setObjectName("label_12")
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.label_12)
        self.gridLayout.addLayout(self.formLayout, 1, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Raindar"))
        self.lineEdit.setText(_translate("MainWindow", "Utrecht,the Netherlands"))
        self.forecastTime1.setText(_translate("MainWindow", "+3h"))
        self.forecastTime2.setText(_translate("MainWindow", "+6h"))
        self.forecastTime3.setText(_translate("MainWindow", "+9h"))
        self.forecastTime4.setText(_translate("MainWindow", "+12h"))
        self.forecastTime5.setText(_translate("MainWindow", "+15h"))
        self.label_5.setText(_translate("MainWindow", "Barometer"))
        self.label_6.setText(_translate("MainWindow", "Temperature"))
        self.label_7.setText(_translate("MainWindow", "Humidity"))
        self.label_8.setText(_translate("MainWindow", "Pressure"))
        self.label.setText(_translate("MainWindow", "Location"))
        self.label_2.setText(_translate("MainWindow", "Longitude"))
        self.label_3.setText(_translate("MainWindow", "Latitude"))
        self.label_4.setText(_translate("MainWindow", "Sunrise"))
        self.label_9.setText(_translate("MainWindow", "Speed"))
        self.label_10.setText(_translate("MainWindow", "Wind"))


    def alert(self, message):
        alert = QMessageBox.warning(self, "Warning", message)

    def update_weather(self):
        worker = WeatherWorker(self.lineEdit.text())
        worker.signals.result.connect(self.weather_result)
        worker.signals.error.connect(self.alert)
        self.threadpool.start(worker)

    def weather_result(self, weather, forecasts):
        self.latitudeLabel.setText("%.2f °" % weather['coord']['lat'])
        self.longitudeLabel.setText("%.2f °" % weather['coord']['lon'])

        self.windLabel.setText("%.2f m/s" % weather['wind']['speed'])

        self.temperatureLabel.setText("%.1f °C" % weather['main']['temp'])
        self.pressureLabel.setText("%d" % weather['main']['pressure'])
        self.humidityLabel.setText("%d" % weather['main']['humidity'])

        self.sunriseLabel.setText(from_ts_to_time_of_day(weather['sys']['sunrise']))

        self.weatherLabel.setText("%s (%s)" % (
            weather['weather'][0]['main'],
            weather['weather'][0]['description']
        )
                                  )

        self.set_weather_icon(self.weatherIcon, weather['weather'])

        for n, forecast in enumerate(forecasts['list'][:5], 1):
            getattr(self, 'forecastTime%d' % n).setText(from_ts_to_time_of_day(forecast['dt']))
            self.set_weather_icon(getattr(self, 'forecastIcon%d' % n), forecast['weather'])
            getattr(self, 'forecastTemp%d' % n).setText("%.1f °C" % forecast['main']['temp'])

    def set_weather_icon(self, label, weather):
        label.setPixmap(QPixmap(os.path.join('images', "%s.png" % weather[0]['icon'])))
        #label.setPixmap(QPixmap('http://openweathermap.org/img/wn/%s@2x.png' % weather[0]['icon']))


if __name__ == '__main__':
    options = argparse.ArgumentParser()
    #options.add_argument("-f", "--file", type=str, required=True)
    args = options.parse_args()

    # Qt Application
    app = QApplication(sys.argv)
    
     # QMainWindow
    window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())
