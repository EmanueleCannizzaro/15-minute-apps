
import json
from urllib import parse
import requests

try:
    from googletrans import Translator
    GOOGLE_TRANSLATE_AVAILABLE = True

except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False

from PySide2.QtCore import (QCoreApplication, QMetaObject, QRect, QSize)
from PySide2.QtGui import (QFont, QIcon, QPixmap)
from PySide2.QtWidgets import (QAction, QApplication, QComboBox, QGridLayout, QHBoxLayout, QLCDNumber, QMenu, QMenuBar, QSizePolicy, QTextEdit, QMainWindow, QPushButton, QStatusBar, QVBoxLayout, QWidget)


LANGUAGES = {
    '<Detect language>': None,
    'Afrikaans': 'af',
    'Albanian': 'sq',
    'Arabic': 'ar',
    'Azerbaijani': 'az',
    'Basque': 'eu',
    'Bengali': 'bn',
    'Belarusian': 'be',
    'Bulgarian': 'bg',
    'Catalan': 'ca',
    'Chinese Simplified': 'zh-CN',
    'Chinese Traditional': 'zh-TW',
    'Croatian': 'hr',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    'Esperanto': 'eo',
    'Estonian': 'et',
    'Filipino': 'tl',
    'Finnish': 'fi',
    'French': 'fr',
    'Galician': 'gl',
    'Georgian': 'ka',
    'German': 'de',
    'Greek': 'el',
    'Gujarati': 'gu',
    'Haitian Creole': 'ht',
    'Hebrew': 'iw',
    'Hindi': 'hi',
    'Hungarian': 'hu',
    'Icelandic': 'is',
    'Indonesian': 'id',
    'Irish': 'ga',
    'Italian': 'it',
    'Japanese': 'ja',
    'Kannada': 'kn',
    'Korean': 'ko',
    'Latin': 'la',
    'Latvian': 'lv',
    'Lithuanian': 'lt',
    'Macedonian': 'mk',
    'Malay': 'ms',
    'Maltese': 'mt',
    'Norwegian': 'no',
    'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Serbian': 'sr',
    'Slovak': 'sk',
    'Slovenian': 'sl',
    'Spanish': 'es',
    'Swahili': 'sw',
    'Swedish': 'sv',
    'Tamil': 'ta',
    'Telugu': 'te',
    'Thai': 'th',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
    'Urdu': 'ur',
    'Vietnamese': 'vi',
    'Welsh': 'cy',
    'Yiddish': 'yi'
}


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.translator = Translator()

        self.destTextEdit.setReadOnly(True)

        if GOOGLE_TRANSLATE_AVAILABLE:
            self.srcLanguage.addItems(tuple(LANGUAGES.keys()))
            self.srcLanguage.currentTextChanged[str].connect(self.update_src_language)
            self.srcLanguage.setCurrentText('English')
        else:
            self.srcLanguage.hide()

        self.translateButton.pressed.connect(self.translate)

        self.show()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(721, 333)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.srcLanguage = QComboBox(self.centralwidget)
        self.srcLanguage.setObjectName("srcLanguage")
        self.verticalLayout.addWidget(self.srcLanguage)
        self.srcTextEdit = QTextEdit(self.centralwidget)
        self.srcTextEdit.setObjectName("srcTextEdit")
        self.verticalLayout.addWidget(self.srcTextEdit)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.translateButton = QPushButton(self.centralwidget)
        self.translateButton.setMinimumSize(QSize(75, 50))
        self.translateButton.setMaximumSize(QSize(75, 50))
        self.translateButton.setText("")
        icon = QIcon()
        icon.addPixmap(QPixmap("images/flag.png"), QIcon.Normal, QIcon.Off)
        self.translateButton.setIcon(icon)
        self.translateButton.setIconSize(QSize(75, 50))
        self.translateButton.setObjectName("translateButton")
        self.verticalLayout_3.addWidget(self.translateButton)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.destTextEdit = QTextEdit(self.centralwidget)
        self.destTextEdit.setObjectName("destTextEdit")
        self.verticalLayout_2.addWidget(self.destTextEdit)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 721, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Translataarrr"))
        self.translateButton.setToolTip(_translate("MainWindow", "Translate"))

    def update_src_language(self, l):
        self.language_src = LANGUAGES[l]

    def google_translate(self, text):
        params = dict(
            dest='en',
            text=text
        )

        if self.language_src:
            params['src'] = self.language_src

        try:
            tr = self.translator.translate(**params)

        except Exception:
            self.destTextEdit.setPlainText('Google translate error :(. Try translating from English')
            return False

        else:
            return tr.text

    def translate(self):
        # Perform pre-translation to English via Google Translate.
        if self.language_src != 'en':
            text = self.google_translate(self.srcTextEdit.toPlainText())
            if not text:
                return False

        # Already in English.
        else:
            text = self.srcTextEdit.toPlainText()

        # Perform translation to piraat.
        r = requests.get(
            'http://api.funtranslations.com/translate/pirate.json?%s' %
            parse.urlencode({'text': text})
        )

        data = json.loads(r.text)
        if 'error' in data:
            self.destTextEdit.setPlainText("%s\n\n%s" % (data['error']['message'], text))
        else:
            self.destTextEdit.setPlainText(data['contents']['translated'])



if __name__ == '__main__':

    app = QApplication([])
    window = MainWindow()
    app.exec_()
