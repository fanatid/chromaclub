from PyQt4 import QtGui

from chromaclub_gui import clubAsset
from application import Application
import sendpage_ui

from chromaclub_gui import clubAsset


class SendPage(QtGui.QWidget, sendpage_ui.Ui_Form):
    def __init__(self, *args, **kwargs):
        QtGui.QWidget.__init__(self, *args, **kwargs)
        self.setupUi(self)

        self._app = Application.instance()
        self._app.wallet.balanceUpdated.connect(self._balance_updated)
        self._app.statusChanged.connect(self._balance_updated)

        self.payToColor.setText(self._app.wallet.get_address(clubAsset['monikers'][0]).split('@')[0] + '@')

        def focusInEvent(event):
            self.payTo.setStyleSheet('')
            QtGui.QLineEdit.focusInEvent(self.payTo, event)
        self.payTo.focusInEvent = focusInEvent

        self._available_check()

    def _available_check(self):
        asset = self._app.wallet.get_asset_definition('bitcoin')

        available = self._app.wallet.get_available_balance(asset)
        unconfirmed = self._app.wallet.get_unconfirmed_balance(asset)

        print available, unconfirmed
        if available >= 10000:
            self.statusLabel.hide()
            self.frame.setEnabled(True)
        else:
            if unconfirmed > 0:
                self.statusLabel.setText(_("Please wait transaction confirmation."))
            else:
                address = self._app.wallet.get_address(asset)
                self.statusLabel.setText(_("For available send coins, please transfer <b>0.1 mBTC</b> to <b>%s</b>") % address)
            self.frame.setDisabled(True)

    def _balance_updated(self):
        self._available_check()

        asset = self._app.wallet.get_asset_definition('bitcoin')

        available = self._app.wallet.get_available_balance(asset)
        unconfirmed = self._app.wallet.get_unconfirmed_balance(asset)

        text = '<b>%s btc</b>' % asset.format_value(available)
        if unconfirmed > 0:
            text += '(pending: <b>%s btc</b>)' % asset.format_value(unconfirmed)

        self.bitcoinBalance.setText(text)

    def on_sendButton_clicked(self, checked=None):
        if checked is None:
            return

        address = str(self.payTo.text())
        if not self._app.wallet.validate_bitcoin_address(address):
            self.payTo.setStyleSheet('background:#FF8080')
            return

        asset = self._app.wallet.get_asset_definition(clubAsset['monikers'][0])
        address = '%s@%s' % (self._app.wallet.get_address(asset).split('@')[0], address)
        self._app.wallet.send_coins(asset, address)
