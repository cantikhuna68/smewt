#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Smewt - A smart collection manager
# Copyright (c) 2008 Ricard Marxer <email@ricardmarxer.com>
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

from smewt import SmewtException, SmewtUrl, Graph, Media, Metadata
from smewt.media import Series, Episode, Movie
from smewt.importtask import ImportTask
from smewt.subtitletask import SubtitleTask
from smewt.taskmanager import Task, TaskManager
from PyQt4.QtCore import SIGNAL, SLOT, QVariant, QProcess, QSettings, pyqtSignature
from PyQt4.QtGui import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QSizePolicy
from PyQt4.QtWebKit import QWebView, QWebPage
from smewt.media import series, movie, speeddial
from bookmarkwidget import BookmarkListWidget
import logging
from os.path import join, dirname, splitext
from smewt.taggers import EpisodeTagger, MovieTagger

log = logging.getLogger('smewt.gui.mainwidget')

class MainWidget(QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.collection = Graph()
        self.connect(self.collection, SIGNAL('updated'),
                     self.refreshCollectionView)
        self.connect(self.collection, SIGNAL('updated'),
                     self.saveCollection)

        self.collectionView = QWebView()
        self.collectionView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        #self.collectionView.page().setLinkDelegationPolicy(QWebPage.DelegateExternalLinks)
        self.connect(self.collectionView,  SIGNAL('linkClicked(const QUrl&)'),
                     self.linkClicked)


        layout = QVBoxLayout()
        layout.addWidget(self.collectionView)

        settings = QSettings()
        t = settings.value('collection_file').toString()
        if t == '':
            t = join(dirname(unicode(settings.fileName())),  'Smewg.collection')
            settings.setValue('collection_file',  QVariant(t))

        try:
            self.collection.load(t)
        except:
            log.warning('Could not load collection %s', t)
            raise

        self.setLayout(layout)

        self.history = []
        self.index = 0
        baseUrl = QSettings().value('base_url').toString()
        if baseUrl == '':
            baseUrl = 'smewt://media/speeddial/'
        self.setSmewtUrl(baseUrl)

        self.externalProcess = QProcess()

        self.taskManager = TaskManager()
        self.connect(self.taskManager, SIGNAL('importFinished'), self.mergeCollection)
        self.connect(self.taskManager, SIGNAL('progressChanged'), self.progressChanged)
        self.connect(self.taskManager, SIGNAL('foundData'), self.mergeCollection)
        

    def back(self):
        self.setSmewtUrl(None, self.index - 1)

    def forward(self):
        self.setSmewtUrl(None, self.index + 1)

    def speedDial(self):
        self.setSmewtUrl(SmewtUrl('media', 'speeddial/'))

    def setSmewtUrl(self, url, index = None):
        if index is not None:
            self.index = min(max(index, 0), len(self.history)-1)
            self.smewtUrl = self.history[self.index]

        else:
            if not isinstance(url, SmewtUrl):
                url = SmewtUrl(url = url)

            self.smewtUrl = url

            self.history[self.index+1:] = []
            self.history.append(url)
            self.index = len(self.history) - 1

        QSettings().setValue('base_url',  QVariant(unicode(self.smewtUrl)))
        self.refreshCollectionView()


    def loadCollection(self):
        filename = str(QFileDialog.getOpenFileName(self, 'Select file to load the collection'))
        self.collection.load(filename)

    def saveCollection(self):
        filename = unicode(QSettings().value('collection_file').toString())
        self.collection.save(filename)

    def importSeriesFolder(self):
        filename = unicode(QFileDialog.getExistingDirectory(self, 'Select directory to import', '/data/Series/',
                                                            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))

        if filename:
            self.importSingleFolder(filename, EpisodeTagger)

    def importMovieFolder(self):
        filename = unicode(QFileDialog.getExistingDirectory(self, 'Select directory to import', '/data/Movies/',
                                                            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))

        if filename:
            self.importSingleFolder(filename, MovieTagger)


    def importSingleFolder(self, path, taggerType):
        filetypes = [ '*.avi',  '*.ogm',  '*.mkv', '*.sub', '*.srt' ]

        importTask = ImportTask(path, taggerType, filetypes = filetypes)
        self.connect(importTask, SIGNAL('foundData'), self.mergeCollection)
        self.taskManager.add( importTask )
        importTask.start()

    def progressChanged(self,  tagged,  total):
        self.emit(SIGNAL('progressChanged'),  tagged,  total)

    def mergeCollection(self, result):
        self.collection += result

    def refreshCollectionView(self):
        surl = self.smewtUrl

        if surl.mediaType == 'speeddial':
            html = speeddial.view.render(surl, self.collection)
            self.collectionView.page().mainFrame().setHtml(html)

        elif surl.mediaType == 'series':
            html = series.view.render(surl, self.collection)
            #open('/tmp/smewt.html',  'w').write(html.encode('utf-8'))
            #print html[:4000]
            self.collectionView.page().mainFrame().setHtml(html)

        elif surl.mediaType == 'movie':
            html = movie.view.render(surl,  self.collection)
            #open('/tmp/smewt.html',  'w').write(html.encode('utf-8'))
            self.collectionView.page().mainFrame().setHtml(html)
            # insert listener object for checkboxes inside the JS environment
            self.connect(self.collectionView.page().mainFrame(), SIGNAL('javaScriptWindowObjectCleared()'),
                         self.connectJavaScript)

        else:
            raise SmewtException('MainWidget: Invalid media type: %s' % surl.mediaType)

    def connectJavaScript(self):
        self.collectionView.page().mainFrame().addToJavaScriptWindowObject('mainWidget', self)

    @pyqtSignature("QString, bool")
    def updateWatched(self, title, watched):
        self.collection.findOne(Movie, title = unicode(title)).watched = watched

    def linkClicked(self,  url):
        log.info('clicked on link %s', url)
        url = url.toEncoded()

        if url.startsWith('file://'):
            action = 'smplayer'
            args = [ str(url)[7:] ]
            log.debug('launching %s with args = %s', (action, args))
            self.externalProcess.start(action, args)

        elif url.startsWith('smewt://'):
            surl = SmewtUrl(url = url)
            if surl.mediaType:
                self.setSmewtUrl(surl)
            elif surl.actionType:
                # TODO: use an ActionFactory to dispatch action to a registered plugin that
                # can provide this type of service, ie: getsubtitles action may be fulfilled
                # by tvsubtitles, opensubtitles, etc...
                if surl.actionType == 'play':
                    action = 'smplayer'
                    args = []
                    nfile = 1
                    while 'filename%d' % nfile in surl.args:
                        args.append(surl.args['filename%d' % nfile])
                        nfile += 1

                    if 'subtitle' in surl.args:
                        args.append(surl.args['subtitle'])
                        
                    log.debug('launching %s with args = %s' % (action, str(args)))
                    self.externalProcess.start(action, args)

                if surl.actionType == 'getsubtitles':
                    series = surl.args['title']
                    language = surl.args['language']
                    episodes = self.collection.findAll(Metadata, series = Series({ 'title': series }))

                    subTask = SubtitleTask(self.collection, episodes, language)
                    self.connect(subTask, SIGNAL('foundData'), self.mergeCollection)
                    self.taskManager.add( subTask )
                    subTask.start()

            else:
                # probably feed watcher
                self.emit(SIGNAL('feedwatcher'))

        else:
            pass

