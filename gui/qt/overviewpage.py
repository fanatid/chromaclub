from PyQt4 import QtGui

from chromaclub_gui import clubAsset
from application import Application
import overviewpage_ui


class OverviewPage(QtGui.QWidget, overviewpage_ui.Ui_Form):
    def __init__(self, *args, **kwargs):
        QtGui.QWidget.__init__(self, *args, **kwargs)
        self.setupUi(self)

        app = Application.instance()
        self._wallet = app.wallet
        self._wallet.balanceUpdated.connect(self._update_widget)
        app.statusChanged.connect(self._update_widget)

    def _update_widget(self):
        moniker = clubAsset['monikers'][0]
        asset = self._wallet.get_asset_definition(moniker)

        address = self._wallet.get_all_addresses(moniker)[0]
        available_balance = self._wallet.get_available_balance(moniker)
        unconfirmed_balance = self._wallet.get_unconfirmed_balance(moniker)
        total_balance = self._wallet.get_total_balance(moniker)

        if available_balance > 0:
            self.labelStatus.hide()
        else:
            if unconfirmed_balance > 0:
                self.labelStatus.setText(_("Please wait transaction confirmation."))
            else:
                self.labelStatus.setText(_("For getting started, please replenish address <b>%s</b>") % address)
            self.labelStatus.show()

        self.labelAddress.setText(address)
        self.labelBalance.setText('%s %s' % (asset.format_value(available_balance), moniker))
        self.labelUnconfirmed.setText('%s %s' % (asset.format_value(unconfirmed_balance), moniker))
        self.labelTotal.setText('%s %s' % (asset.format_value(total_balance), moniker))
