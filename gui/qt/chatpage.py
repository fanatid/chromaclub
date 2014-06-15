import time
import Queue
import threading
import urllib2
import json

from PyQt4 import QtCore, QtGui

from chromaclub_gui import clubAsset
from application import Application
import chatpage_ui

from chromaclub_gui import clubAsset


class MessageWatcher(threading.Thread):
    SERVICE_URL = "http://localhost:28833/"

    def __init__(self, chatpage, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)

        self.chatpage = chatpage
        self._running = False
        self.lock = threading.Lock()
        self.txQ, self.rxQ = Queue.Queue(), Queue.Queue()
        self._wallet = Application.instance().wallet
        self._lastId = -1

    def is_running(self):
        with self.lock:
            return self._running

    def stop(self):
        with self.lock:
            self._running = False

    def _make_request(self, method, params=None):
        data = json.dumps({
            'method': method,
            'params': {} if params is None else params,
        })
        request = urllib2.Request(self.SERVICE_URL, data)
        try:
            return json.loads(urllib2.urlopen(request).read())
        except urllib2.HTTPError, e:
            print(e.code, e.read())
            raise

    def _run_once(self):
        auth_data = self._wallet.get_auth_data(clubAsset['monikers'][0])

        try:
            data = self.txQ.get_nowait()
            self._make_request('addmessage', {
                'color_set': auth_data['color_set'],
                'txhash':    auth_data['txhash'],
                'outindex':  auth_data['outindex'],
                'pubkey':    auth_data['pubkey'],
                'data':      data['message'],
                'sign':      self._wallet.sign_data(data['message'], auth_data['privkey']),
            })
        except Queue.Empty:
            pass

        data = self._make_request('getmessages', {
            'color_set': auth_data['color_set'],
            'txhash':    auth_data['txhash'],
            'outindex':  auth_data['outindex'],
            'pubkey':    auth_data['pubkey'],
            'data':      self._lastId,
            'sign':      self._wallet.sign_data(self._lastId, auth_data['privkey']),
        })
        if not data:
            return

        for item in data:
            self._lastId = item[0]
            self.rxQ.put({
                'address': item[1],
                'message': item[2],
            })

    def run(self):
        with self.lock:
            self._running = True

        wakeup = 0
        while self.is_running():
            if wakeup > time.time():
                time.sleep(0.05)
                continue

            try:
                self._run_once()
            except Exception as e:
                print(e)

            wakeup = time.time() + 1


class ChatPage(QtGui.QWidget, chatpage_ui.Ui_Form):
    def __init__(self, *args, **kwargs):
        QtGui.QWidget.__init__(self, *args, **kwargs)
        self.setupUi(self)

        app = Application.instance()
        app.statusChanged.connect(self._status_changed)
        self._wallet = app.wallet

        self._watcher = MessageWatcher(self)
        self.serviceURL.setText(self._watcher.SERVICE_URL)

        self._newMessageWatcher = QtCore.QTimer()
        self._newMessageWatcher.setInterval(50)
        self._newMessageWatcher.timeout.connect(self._check_new_messages)

    def on_chatMessage_returnPressed(self):
        self.sendButton.click()

    def on_sendButton_clicked(self, checked=None):
        if checked is None:
            return
        message = str(self.chatMessage.text())
        self.chatMessage.setText('')
        if not message:
            return

        self._watcher.txQ.put({
            'message': message,
        })

    def _status_changed(self, oldStatus, newStatus):
        if newStatus == Application.STATUS_WORK:
            self.sendButton.setEnabled(True)
            self.sync_start()
        else:
            self.sendButton.setEnabled(False)
            self.sync_stop()

    def _check_new_messages(self):
        try:
            while True:
                item = self._watcher.rxQ.get_nowait()
                address = item['address']
                if address == self._wallet.get_bitcoin_address(clubAsset['monikers'][0]):
                    address = '<b>%s</b>' % address
                text = item['message']
                self.chatField.append('<html><body>%s: %s</body></html>' % (address, text,))
        except Queue.Empty:
            pass

    def sync_start(self):
        self._watcher.start()
        self._newMessageWatcher.start()

    def sync_stop(self):
        self._watcher.stop()
        self._newMessageWatcher.stop()
