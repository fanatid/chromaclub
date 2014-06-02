from PyQt4 import QtGui

from chromaclub_gui import clubAsset
from application import Application
import chatpage_ui


class ChatPage(QtGui.QWidget, chatpage_ui.Ui_Form):
    def __init__(self, *args, **kwargs):
        QtGui.QWidget.__init__(self, *args, **kwargs)
        self.setupUi(self)

    def on_sendButton_clicked(self, checked=None):
        if checked is None:
            return
        print self
