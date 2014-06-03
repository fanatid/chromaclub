from PyQt4 import QtCore, QtGui


class Application(QtGui.QApplication):
    STATUS_REPLENISH = 0
    STATUS_CONFIRMATION = 1
    STATUS_WORK = 2

    statusChanged = QtCore.pyqtSignal(int, int, name='changeStatus')

    def __init__(self, args):
        QtGui.QApplication.__init__(self, [])
        self.isTestNet = args['testnet']
        self.dataDir = args['datadir']
        self._status = None

    def _install_i18n(self):
        import __builtin__
        __builtin__.__dict__["_"] = lambda x: x

    def exec_(self):
        self._install_i18n()

        from wallet import Wallet
        self.wallet = Wallet(self.dataDir, self.isTestNet)
        self.wallet.balanceUpdated.connect(self._check_status)

        from mainwindow import MainWindow
        self.mainWindow = MainWindow()
        self.mainWindow.show()

        self.wallet.sync_start()
        QtCore.QTimer.singleShot(0, self._check_status)
        # Todo: remove
        #self.mainWindow.chatAction.trigger()
        #self.mainWindow.chatpage.chatMessage.setText('new message')
        # ----
        retval = super(QtGui.QApplication, self).exec_()
        self.mainWindow.chatpage.sync_stop()
        self.wallet.sync_stop()
        return retval

    def _check_status(self):
        available_balance = self.wallet.get_available_balance()
        unconfirmed_balance = self.wallet.get_unconfirmed_balance()

        if available_balance > 0:
            self._set_new_status(self.STATUS_WORK)
        else:
            if unconfirmed_balance > 0:
                self._set_new_status(self.STATUS_CONFIRMATION)
            else:
                self._set_new_status(self.STATUS_REPLENISH)

    def _set_new_status(self, status):
        if self._status == status:
            return
        oldStatus = self._status
        self._status = status
        self.statusChanged.emit(oldStatus, status)
