import os

from PyQt4 import QtCore

from ngcccbase.pwallet import PersistentWallet
from ngcccbase.wallet_controller import WalletController
from ngcccbase.asset import AssetDefinition
from ngcccbase.utxo_fetcher import AsyncUTXOFetcher
from ngcccbase.txdb import BaseTxDb


class Wallet(QtCore.QObject):
    balanceUpdated = QtCore.pyqtSignal(name='balanceUpdated')

    def __init__(self, dataDir, isTestNet):
        QtCore.QObject.__init__(self)

        self._patching_BaseTxDb()

        self._pwallet = PersistentWallet(os.path.join(dataDir, 'wallet.sqlite'), isTestNet)
        self._set_wallet_settings(dataDir, isTestNet)
        self._pwallet.init_model()
        self._wallet = self._pwallet.get_model()
        self._controller = WalletController(self._wallet)
        self._utxo_fetcher = AsyncUTXOFetcher(
            self._wallet, self._pwallet.wallet_config.get('utxo_fetcher', {}))

        self._utxo_fetcher_timer = QtCore.QTimer()
        self._utxo_fetcher_timer.timeout.connect(self._utxo_fetcher.update)
        self._utxo_fetcher_timer.setInterval(1000)

    def _patching_BaseTxDb(self):
        original_add_tx = BaseTxDb.add_tx
        def new_add_tx(baseTxDb, txhash, txdata, raw_tx, *args, **kwargs):
            retval = original_add_tx(baseTxDb, txhash, txdata, raw_tx, *args, **kwargs)

            if retval:
                ctxs = raw_tx.composed_tx_spec
                coinStore = self._wallet.get_coin_manager().store
                all_addresses = [a.get_address() for a in
                    self._wallet.get_address_manager().get_all_addresses()]
                lookup_moniker_by_address = {}
                for asset in self._controller.get_all_assets():
                    monikers = asset.get_monikers()
                    for address in self._controller.get_all_addresses(asset):
                        lookup_moniker_by_address[address.get_address()] = monikers
                # txin
                for txin in ctxs.txins:
                    prev_txhash, prev_outindex = txin.get_outpoint()
                    coin_id = coinStore.find_coin(prev_txhash, prev_outindex)
                    if coin_id:
                        address = coinStore.get_coin(coin_id)['address']
                        self.balanceUpdated.emit()
                # txout
                for txout in ctxs.txouts:
                    target_addr = txout.target_addr
                    if target_addr in all_addresses:
                        self.balanceUpdated.emit()

            return retval
        BaseTxDb.add_tx = new_add_tx

    def _set_wallet_settings(self, dataDir, isTestNet):
        self._pwallet.wallet_config['testnet'] = isTestNet

        ccc = self._pwallet.wallet_config.get('ccc', {})
        ccc['colordb_path'] = os.path.join(dataDir, 'color_db.sqlite')
        self._pwallet.wallet_config['ccc'] = ccc

    def sync_start(self):
        self._utxo_fetcher.start_thread()
        self._utxo_fetcher_timer.start()

    def sync_stop(self):
        self._utxo_fetcher.stop()
        self._utxo_fetcher_timer.stop()

    def get_model(self):
        return self._wallet

    def get_asset_definition(self, moniker):
        if isinstance(moniker, AssetDefinition):
            return moniker
        adm = self._wallet.get_asset_definition_manager()
        asset = adm.get_asset_by_moniker(moniker)
        if not asset:
            raise Exception("asset not found")
        return asset

    def get_all_monikers(self):
        assets = self._wallet.get_asset_definition_manager().get_all_assets()
        return sum([asset.get_monikers() for asset in assets], [])

    def get_all_addresses(self, moniker):
        asset = self.get_asset_definition(moniker)
        return [addr.get_color_address()
                for addr in self._controller.get_all_addresses(asset)]

    def add_asset_definition(self, params):
        for asset in self._wallet.get_asset_definition_manager().get_all_assets():
            for color in asset.get_color_set().get_data():
                if color in params['color_set']:
                    return
        self._wallet.get_asset_definition_manager().add_asset_definition(params)
        assdef = self.get_asset_definition(params['monikers'][0])
        if len(self._controller.get_all_addresses(assdef)) == 0:
            self.create_new_address(params['monikers'][0])

    def create_new_address(self, moniker):
        asset = self.get_asset_definition(moniker)
        self._controller.get_new_address(asset).get_color_address()

    def get_total_balance(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_total_balance(asset)

    def get_available_balance(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_available_balance(asset)

    def get_unconfirmed_balance(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_unconfirmed_balance(asset)
