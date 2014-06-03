from PyQt4 import QtCore, QtGui

from chromaclub_gui import clubAsset
from application import Application
from overviewpage import OverviewPage
from chatpage import ChatPage


def checkPoint(point, widget):
    atW = Application.widgetAt(widget.mapToGlobal(point))
    if not atW:
        return False
    return atW.topLevelWidget() == widget

def isObscured(widget):
    return not (checkPoint(QtCore.QPoint(0, 0), widget)
        and checkPoint(QtCore.QPoint(widget.width()-1, 0), widget)
        and checkPoint(QtCore.QPoint(0, widget.height()-1), widget)
        and checkPoint(QtCore.QPoint(widget.width()-1, widget.height()-1), widget)
        and checkPoint(QtCore.QPoint(widget.width()/2, widget.height()/2), widget))

class MainWindow(QtGui.QMainWindow):
    def __init__(self, *args, **kwargs):
        QtGui.QMainWindow.__init__(self, *args, **kwargs)

        self._app = Application.instance()

        title = "ChromaClub"
        if self._app.isTestNet:
            title += " [testnet]"
        title += " - " + clubAsset['monikers'][0]
        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(':icons/chromaclub.png'))
        self.resize(900, 550)
        self.move(Application.instance().desktop().screen().rect().center() - self.rect().center())
        self.setCentralWidget(QtGui.QStackedWidget())

        self.overviewpage = OverviewPage(self)
        self.chatpage = ChatPage(self)
        self.centralWidget().addWidget(self.overviewpage)
        self.centralWidget().addWidget(self.chatpage)

        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_tray_icon()
        self._create_tray_icon_menu()

        self._app.statusChanged.connect(self._status_changed)

    def _create_actions(self):
        tabGroup = QtGui.QActionGroup(self)

        self.overviewAction = QtGui.QAction(QtGui.QIcon(':icons/overview.png'), _("&Overview"), self)
        self.overviewAction.setStatusTip(_("Show general overview of wallet"))
        self.overviewAction.setToolTip(self.overviewAction.statusTip())
        self.overviewAction.setCheckable(True)
        self.overviewAction.setChecked(True)
        self.overviewAction.triggered.connect(self.show_normal_if_minimized)
        self.overviewAction.triggered.connect(lambda:
            self.centralWidget().setCurrentWidget(self.overviewpage))
        tabGroup.addAction(self.overviewAction)

        self.chatAction = QtGui.QAction(QtGui.QIcon(':icons/chat.png'), _("&Chat"), self)
        self.chatAction.setStatusTip(_("Show chromaclub chat"))
        self.chatAction.setToolTip(self.chatAction.statusTip())
        self.chatAction.setCheckable(True)
        self.chatAction.triggered.connect(self.show_normal_if_minimized)
        self.chatAction.triggered.connect(lambda:
            self.centralWidget().setCurrentWidget(self.chatpage))
        tabGroup.addAction(self.chatAction)

        self.quitAction = QtGui.QAction(QtGui.QIcon(':icons/exit.png'), _("E&xit"), self)
        self.quitAction.setStatusTip(_("Quit application"))
        self.quitAction.setToolTip(self.quitAction.statusTip())
        self.quitAction.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Q))
        self.quitAction.setMenuRole(QtGui.QAction.QuitRole)
        self.quitAction.triggered.connect(self._app.quit)

        self.toggleHideAction = QtGui.QAction(QtGui.QIcon(':icons/chromaclub.png'), _("&Show / Hide"), self)
        self.toggleHideAction.setStatusTip(_("Show or hide the main Window"))
        self.toggleHideAction.triggered.connect(lambda *args:
            self.show_normal_if_minimized(*(list(args) + [True])))

    def _create_menu_bar(self):
        menuBar = self.menuBar()

        file = menuBar.addMenu(_("&File"))
        file.addAction(self.quitAction)

    def _create_tool_bar(self):
        toolBar = self.toolBar = self.addToolBar("Tabs toolbar")
        toolBar.setIconSize(QtCore.QSize(40, 40))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        toolBar.addAction(self.overviewAction)
        toolBar.addAction(self.chatAction)

    def _create_status_bar(self):
        statusBar = self.statusBar()

    def _create_tray_icon(self):
        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setIcon(QtGui.QIcon(':icons/chromaclub.png'))
        self.trayIcon.setToolTip(_("ChromaClub") +
            (" [testnet]" if Application.instance().isTestNet else ""))
        def activated(reason):
            if reason == QtGui.QSystemTrayIcon.Trigger:
                self.toggleHideAction.trigger()
        self.trayIcon.activated.connect(activated)
        self.trayIcon.show()

    def _create_tray_icon_menu(self):
        menu = QtGui.QMenu(self)

        menu.addAction(self.toggleHideAction)
        menu.addSeparator()
        menu.addAction(self.quitAction)

        self.trayIcon.setContextMenu(menu)

    def show_normal_if_minimized(self, checked, toggleHidden=False):
        if self.isHidden():
            self.show()
            self.activateWindow()
        elif self.isMinimized():
            self.showNormal()
            self.activateWindow()
        elif isObscured(self):
            self.raise_()
            self.activateWindow()
        elif toggleHidden:
            self.hide()

    def _status_changed(self, oldStatus, newStatus):
        if newStatus == self._app.STATUS_WORK:
            self.toolBar.show()
        else:
            self.toolBar.hide()
