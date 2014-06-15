import os
import threading
import string
import random
from hashlib import sha256

from PyQt4 import QtCore

from pycoin import ecdsa
from pycoin.encoding import public_pair_to_sec, hash160, a2b_base58

from ngcccbase.pwallet import PersistentWallet
from ngcccbase.wallet_controller import WalletController
from ngcccbase.asset import AssetDefinition
from ngcccbase.utxo_fetcher import AsyncUTXOFetcher
from ngcccbase.txdb import BaseTxDb

from chromaclub_gui import clubAsset


class Wallet(QtCore.QObject):
    balanceUpdated = QtCore.pyqtSignal(name='balanceUpdated')

    def __init__(self, dataDir, isTestNet):
        QtCore.QObject.__init__(self)

        self.lock = threading.Lock()

        self._patching_BaseTxDb()

        self.wallet_path = os.path.join(dataDir, 'wallet.sqlite')
        self._pwallet = PersistentWallet(self.wallet_path, isTestNet)
        self._set_wallet_settings(dataDir, isTestNet)
        self._pwallet.init_model()
        self._wallet = self._pwallet.get_model()
        self._controller = WalletController(self._wallet)
        self._utxo_fetcher = AsyncUTXOFetcher(
            self._wallet, self._pwallet.wallet_config.get('utxo_fetcher', {}))

        self._utxo_fetcher_timer = QtCore.QTimer()
        self._utxo_fetcher_timer.timeout.connect(self._utxo_fetcher.update)
        self._utxo_fetcher_timer.setInterval(1000)

        asset = self.get_asset_definition('bitcoin')
        if len(self._controller.get_all_addresses(asset)) == 0:
            self._controller.get_new_address(asset)

        self._create_club_asset()

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

    def _create_club_asset(self):
        for asset in self._wallet.get_asset_definition_manager().get_all_assets():
            for color in asset.get_color_set().get_data():
                if color in clubAsset['color_set']:
                    return
        self._wallet.get_asset_definition_manager().add_asset_definition(clubAsset)
        asset = self.get_asset_definition(clubAsset['monikers'][0])
        if len(self._controller.get_all_addresses(asset)) == 0:
            self._controller.get_new_address(asset).get_color_address()

    def sync_start(self):
        self._utxo_fetcher.start_thread()
        self._utxo_fetcher_timer.start()

    def sync_stop(self):
        self._utxo_fetcher.stop()
        self._utxo_fetcher_timer.stop()

    def get_asset_definition(self, moniker):
        if isinstance(moniker, AssetDefinition):
            return moniker
        adm = self._wallet.get_asset_definition_manager()
        asset = adm.get_asset_by_moniker(moniker)
        if not asset:
            raise Exception("asset not found")
        return asset

    def get_address(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_all_addresses(asset)[0].get_color_address()

    def get_bitcoin_address(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_all_addresses(asset)[0].get_address()

    def get_total_balance(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_total_balance(asset)

    def get_available_balance(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_available_balance(asset)

    def get_unconfirmed_balance(self, moniker):
        asset = self.get_asset_definition(moniker)
        return self._controller.get_unconfirmed_balance(asset)

    def send_coins(self, moniker, address):
        asset = self.get_asset_definition(moniker)
        total = self.get_total_balance(asset)
        self._controller.send_coins(asset, [address], [total])

    def get_auth_data(self, moniker):
        with self.lock:
            coin = self._wallet.make_coin_query({
                'asset': self.get_asset_definition(moniker),
                'spent': False,
            }).get_result()[0]
            pubKey = public_pair_to_sec(coin.address_rec.publicPoint.pair(), compressed=False)
            return {
                'color_set':   clubAsset['color_set'][0],
                'txhash':      coin.txhash,
                'outindex':    coin.outindex,
                'pubkey':      pubKey.encode('hex'),
                'privkey':     coin.address_rec.rawPrivKey,
                'address_rec': coin.address_rec,
            }

    def sign_data(self, data, privKey):
        with self.lock:
            symbols_set = string.ascii_letters + string.digits
            salt = ''.join([random.choice(symbols_set) for _ in xrange(20)])
            data = int((hash160(str(data) + salt)).encode('hex'), 16)
            return {
                'salt': salt,
                'sign': ecdsa.sign(ecdsa.generator_secp256k1, privKey, data),
            }

    def validate_bitcoin_address(self, address):
        bcbytes = a2b_base58(str(address))
        return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
