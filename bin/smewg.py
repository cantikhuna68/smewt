#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Smewt - A smart collection manager
# Copyright (c) 2008 Nicolas Wack <wackou@gmail.com>
#
# Smewt is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Smewt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys, logging, os, os.path

MAIN_LOGGING_LEVEL = logging.INFO


from utils.slogging import setupLogging
setupLogging()

logging.getLogger().setLevel(MAIN_LOGGING_LEVEL)

# we most likely never want this to be on debug mode, as it spits out way too much information
if MAIN_LOGGING_LEVEL == logging.DEBUG:
    logging.getLogger('pygoo').setLevel(logging.INFO)
    logging.getLogger('imdbpy').setLevel(logging.INFO)


# need that before importing any other module when Smewt is installed
# FIXME: do we still need this?
if sys.platform == 'win32':
    SMEWT_ROOT = os.path.split(os.path.abspath(__file__))[0]
    sys.path = [ SMEWT_ROOT + '\\site-packages' ] + sys.path


from PyQt4.QtGui import QApplication, QMainWindow, QWidget, QStatusBar, QProgressBar, QHBoxLayout, QStackedWidget, QIcon, QSystemTrayIcon, QAction, QMenu, QMessageBox, QToolBar
from PyQt4.QtCore import SIGNAL, QSize, Qt, QSettings, QVariant, QPoint, QSize, QObject, QTimer
from smewt.gui import MainWidget, FeedWatchWidget
from smewt.base import cache, utils
from smewt.base.utils import smewtDirectory
from os.path import join

log = logging.getLogger('smewg')
DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 740


class StatusWidget(QWidget):
    def __init__(self):
        super(QWidget,  self).__init__()

        layout = QHBoxLayout()
        layout.addStretch()

        self.progressBar = QProgressBar()

        layout.addWidget(self.progressBar)

        self.setLayout(layout)
        return

class SmewtGui(QMainWindow):

    def __init__(self):
        super(SmewtGui, self).__init__()
        self.setWindowTitle('Smewg - An Ordinary Smewt Gui')

        self.readWindowSettings()

        self.icon = QIcon(smewtDirectory('smewt', 'icons', 'smewt.svg'))
        self.setWindowIcon(self.icon)

        self.createWidgets()
        self.createActions()

        # create menubar
        mainMenu = self.menuBar().addMenu('Main')
        mainMenu.addAction(self.clearCacheAction)
        mainMenu.addSeparator()
        mainMenu.addAction(self.quitAction)

        importMenu = self.menuBar().addMenu('Collection')
        importMenu.addAction(self.selectMoviesFoldersAction)
        importMenu.addAction(self.selectSeriesFoldersAction)
        importMenu.addSeparator()
        importMenu.addAction(self.updateCollectionAction)
        importMenu.addAction(self.rescanCollectionAction)

        helpMenu = self.menuBar().addMenu('Help')
        helpMenu.addAction(self.aboutAction)
        helpMenu.addAction(self.aboutQtAction)

        # create toolbar
        navigationToolBar = QToolBar('Navigation')
        navigationToolBar.addAction(self.backAction)
        navigationToolBar.addAction(self.fwdAction)
        navigationToolBar.addAction(self.refreshAction)
        navigationToolBar.addAction(self.homeAction)
        navigationToolBar.addSeparator()
        navigationToolBar.addAction(self.zoomOutAction)
        navigationToolBar.addAction(self.zoomInAction)
        navigationToolBar.addSeparator()
        navigationToolBar.addAction(self.fullScreenAction)
        navigationToolBar.setIconSize(QSize(32,32))
        navigationToolBar.setObjectName('navigationToolBar')
        self.addToolBar(navigationToolBar)
        self.createTrayIcon()

        # tmp
        self.connect(self.mainWidget, SIGNAL('feedwatcher'),
                     self.showFeedWatcher)

        # first-run wizard
        settings = QSettings()
        configured = settings.value('configured').toBool()

        if not configured:
            settings.setValue('configured', True)
            QTimer.singleShot(0, self.firstRun)
        else:
            # only start the update of the collections once our GUI is fully setup
            # do not rescan as it would be too long and we might delete some files that
            # are on an unaccessible network share or an external HDD
            QTimer.singleShot(2000, self.reloadCacheAndUpdateCollections)


    def showFeedWatcher(self):
        self.tabWidget.setCurrentIndex(1)

    def showSpeedDial(self):
        self.tabWidget.setCurrentIndex(0)
        self.mainWidget.speedDial()

    def createWidgets(self):
        self.mainWidget = MainWidget()
        self.feedWatchWidget = FeedWatchWidget()

        self.tabWidget = QStackedWidget()
        self.tabWidget.addWidget(self.mainWidget)
        self.tabWidget.addWidget(self.feedWatchWidget)

        self.setCentralWidget(self.tabWidget)

        self.statusWidget = StatusWidget()
        self.statusBar().addPermanentWidget(self.statusWidget)


        self.mainWidget.smewtd.taskManager.progressChanged.connect(self.progressChanged)

    def createActions(self):
        self.clearCacheAction = QAction('Clear internet cache', self)
        self.connect(self.clearCacheAction, SIGNAL('triggered()'),
                     self.clearCache)

        self.quitAction = QAction('Quit', self)
        self.connect(self.quitAction, SIGNAL('triggered()'),
                     self.quit)

        self.minimizeAction = QAction('Minimize', self)
        self.connect(self.minimizeAction, SIGNAL('triggered()'),
                     self.hide)

        self.restoreAction = QAction('Restore', self)
        self.connect(self.restoreAction, SIGNAL('triggered()'),
                     self.showNormal)

        self.aboutAction = QAction('About', self)
        self.connect(self.aboutAction, SIGNAL('triggered()'),
                     self.about)

        self.aboutQtAction = QAction('About Qt', self)
        self.connect(self.aboutQtAction, SIGNAL('triggered()'),
                     self.aboutQt)


        # navigation bar
        self.backAction = QAction(QIcon(smewtDirectory('smewt', 'icons', 'go-previous.png')), 'Back', self)
        self.backAction.setStatusTip('Go back')
        self.connect(self.backAction, SIGNAL('triggered()'),
                     self.mainWidget.back)

        self.fwdAction = QAction(QIcon(smewtDirectory('smewt', 'icons', 'go-next.png')), 'Forward', self)
        self.fwdAction.setStatusTip('Go forward')
        self.connect(self.fwdAction, SIGNAL('triggered()'),
                     self.mainWidget.forward)

        self.refreshAction = QAction(QIcon(smewtDirectory('smewt', 'icons', 'view-refresh.png')), 'Refresh', self)
        self.refreshAction.setStatusTip('Refresh the main view')
        self.connect(self.refreshAction, SIGNAL('triggered()'),
                     self.mainWidget.refreshCollectionView)

        self.homeAction = QAction(QIcon(smewtDirectory('smewt', 'icons', 'go-home.png')), 'Home (Speed Dial)', self)
        self.homeAction.setStatusTip('Return to speed dial')
        self.connect(self.homeAction, SIGNAL('triggered()'),
                     self.showSpeedDial)


        self.zoomInAction = QAction(QIcon(smewtDirectory('smewt', 'icons', 'zoom-in.png')), 'Zoom in', self)
        self.zoomInAction.setStatusTip('Make the text larger')
        self.connect(self.zoomInAction, SIGNAL('triggered()'),
                     self.mainWidget.zoomIn)

        self.zoomOutAction = QAction(QIcon(smewtDirectory('smewt', 'icons', 'zoom-out.png')), 'Zoom out', self)
        self.zoomOutAction.setStatusTip('Make the text smaller')
        self.connect(self.zoomOutAction, SIGNAL('triggered()'),
                     self.mainWidget.zoomOut)

        self.fullScreenAction = QAction(QIcon(smewtDirectory('smewt', 'icons', 'view-fullscreen.png')), 'Full Screen', self)
        self.fullScreenAction.setStatusTip('Toggle fullscreen mode')
        self.fullScreenAction.setCheckable(True)
        self.connect(self.fullScreenAction, SIGNAL('triggered()'),
                     self.toggleFullScreen)

        # import actions

        self.selectMoviesFoldersAction = QAction('Select movies folders', self)
        self.selectMoviesFoldersAction.setStatusTip('Select the folders containing movies')
        self.connect(self.selectMoviesFoldersAction,  SIGNAL('triggered()'),
                     self.mainWidget.selectMoviesFolders)

        self.selectSeriesFoldersAction = QAction('Select series folders', self)
        self.selectSeriesFoldersAction.setStatusTip('Select the folders containing series')
        self.connect(self.selectSeriesFoldersAction,  SIGNAL('triggered()'),
                     self.mainWidget.selectSeriesFolders)

        self.updateCollectionAction = QAction('Update collection', self)
        self.updateCollectionAction.setStatusTip('Update the collection')
        self.connect(self.updateCollectionAction,  SIGNAL('triggered()'),
                     self.mainWidget.updateCollection)

        self.rescanCollectionAction = QAction('Rescan collection', self)
        self.rescanCollectionAction.setStatusTip('Rescan the collection')
        self.connect(self.rescanCollectionAction,  SIGNAL('triggered()'),
                     self.mainWidget.rescanCollection)

    def toggleFullScreen(self):
        flag = Qt.WindowFullScreen if self.fullScreenAction.isChecked() else ~Qt.WindowFullScreen
        self.setWindowState(self.windowState() ^ Qt.WindowFullScreen  )

    def reloadCacheAndUpdateCollections(self):
        # do this now instead of at the very beginning so that our GUI can be setup faster
        cache.load(utils.smewtUserPath(smewt.APP_NAME + '.cache'))
        self.mainWidget.smewtd.updateCollections()

    def clearCache(self):
        cache.clear()
        cacheFile = utils.smewtUserPath(smewt.APP_NAME + '.cache')
        log.info('Deleting cache file: %s' % cacheFile)
        os.remove(cacheFile)

    def quit(self):
        log.info('SmewtGui quitting...')
        self.writeWindowSettings()
        self.mainWidget.quit()

        # save cache
        cache.save(utils.smewtUserPath(smewt.APP_NAME + '.cache'))

        log.info('Quitting application...')
        QApplication.instance().quit()

    def readWindowSettings(self):
        settings = QSettings()
        pos = settings.value("MainWindow/pos", QVariant(QPoint((QApplication.desktop().width()-DEFAULT_WIDTH)/2, (QApplication.desktop().width()-DEFAULT_HEIGHT)/2))).toPoint()
        size = settings.value("MainWindow/size", QVariant(QSize(DEFAULT_WIDTH, DEFAULT_HEIGHT))).toSize()
        self.resize(size)
        self.move(pos)

        self.restoreState(settings.value("MainWindow/windowstate").toByteArray())

    def writeWindowSettings(self):
        settings = QSettings()
        settings.setValue("MainWindow/pos", QVariant(self.pos()))
        settings.setValue("MainWindow/size", QVariant(self.size()))

        settings.setValue("MainWindow/windowstate", QVariant(self.saveState()))


    def createTrayIcon(self):
        trayMenu = QMenu(self)
        trayMenu.addAction(self.minimizeAction)
        trayMenu.addAction(self.restoreAction)
        trayMenu.addSeparator()
        trayMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self.icon, self)
        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.setVisible(True)

        self.connect(self.trayIcon, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'),
                     self.iconActivated)

    def setVisible(self, visible):
        self.minimizeAction.setEnabled(visible)
        self.restoreAction.setEnabled(not visible)
        QMainWindow.setVisible(self, visible)


    def iconActivated(self, reason):
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.setVisible(False)
            else:
                self.setVisible(True)

    def closeEvent(self, event):
        self.writeWindowSettings()
        self.hide()
        event.ignore()

    def progressChanged(self,  tagged,  total):
        from threading import current_thread
        log.debug('Received signal in thread %d' % current_thread().ident)

        if total == 0:
            log.debug('Resetting progress bar')
            self.statusWidget.progressBar.reset()
        else:
            log.debug('Setting progress bar to %d/%d' % (tagged, total))
            self.statusWidget.progressBar.setMaximum(total)
            self.statusWidget.progressBar.setValue(tagged)

    def firstRun(self):
        QMessageBox.about(self, 'First run wizard',
'''                Smewt - a smart media manager

It looks like it is the first time you run Smewt. Smewt is
intended to be very easy and intuitive to use, and pretty
much everything should be automatic and will run without
your supervision.

There are however a few steps you need to do to get you
started. As you probably already know, Smewt is a media
manager, which means that it will take care of organizing
your media files (movies, TV shows, ...) in a nice way and
make it easier for you to browse through them.

In order to do this, you should tell Smewt where to find
your files:

 - Open the Collection menu, and select the folder(s)
   where your movies are located

 - Open the Collection menu, and select the folder(s)
   where your TV shows are located

As soon as you have done this, Smewt will look for files in
these folders, and import them into your collection.
A progress bar at the bottom will indicate the status of this
operation. When this completes, Smewt will be ready to use.

We hope you will enjoy using Smewt!

The Smewt developers.
''')

    def about(self):
        QMessageBox.about(self, 'About Smewt',
'''Smewt - a smart media manager

(c) 2008-2011 Nicolas Wack, Ricard Marxer
GPLv3 licensed''')

    def aboutQt(self):
        QMessageBox.aboutQt(self)


if __name__ == '__main__':
    import smewt
    app = QApplication(sys.argv)
    app.setOrganizationName(smewt.ORG_NAME)
    app.setOrganizationDomain('smewt.com')
    app.setApplicationName(smewt.APP_NAME)

    sgui = SmewtGui()

    sgui.show()
    app.exec_()

    log.info('Exiting')
    sys.exit() # why is this necessary when running from eric?