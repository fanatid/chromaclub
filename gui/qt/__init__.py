from PyQt4 import QtCore

import icons_rc
from application import Application


class QtUI(object):
    def __init__(self, args):
        self.args = args

    def start(self):
        app = Application(self.args)

        name = "chromaclub"
        app.setOrganizationName(name)
        #app.setOrganizationDomain("") # Todo?
        app.setApplicationName(app.organizationName() + "-qt" +
            ("-testnet" if self.args['testnet'] else ""))

        app.exec_()
