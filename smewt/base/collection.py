#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Smewt - A smart collection manager
# Copyright (c) 2011 Nicolas Wack <wackou@gmail.com>
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

import logging
import time, os

from PyQt4.QtCore import QObject, SIGNAL, QVariant, QSettings
from pygoo import MemoryObjectGraph, ontology

from smewt.base import utils, Media, Metadata
from smewt.base import ImportTask, SubtitleTask
from smewt.taggers import EpisodeTagger, MovieTagger
from smewt.base.textutils import toUtf8

log = logging.getLogger('smewt.base.collection')

class Collection(object):
    """A Collection keeps track of the files in the folders for us. when any changes
    happen there, it creates new import tasks for new files or removes references to
    deleted files."""

    def __init__(self, name, validFiles, mediaTagger, dataGraph, taskManager, folders = {}):
        # identifies the collection
        self.name = name
        # validFiles is a list of conditions a file should meet to be considered to belong to this collection
        self.validFiles = validFiles
        self.mediaTagger = mediaTagger

        self.graph = dataGraph
        self.taskManager = taskManager

        # folders is a dict of folder names to bool indicating whether they should be traversed recursively
        self.folders = folders

        # files is a dict of filenames to last time they were updated
        self.files = {}

        self.loadSettings()


    def loadSettings(self):
        settings = QSettings()
        collection = settings.value('collection_%s' % self.name).toList()
        if collection:
            self.folders = dict((toUtf8(folder), recursive.toBool()) for folder, recursive in collection[0].toMap().items())
            self.files = dict((toUtf8(file), lastAccessed.toInt()[0]) for file, lastAccessed in collection[1].toMap().items())

    def saveSettings(self):
        QSettings().setValue('collection_%s' % self.name, QVariant([ QVariant(self.folders), QVariant(self.files) ]))


    def checkIntegrity():
        # delete files in set(files) - set(dirwalk())
        pass


    def setFolders(self, folders):
        self.folders = folders

        self.saveSettings()
        self.update()


    def collectionFiles(self):
        for folder, recursive in self.folders.items():
            for f in utils.dirwalk(folder, self.validFiles, recursive):
                yield f

    def modifiedFiles(self):
        for f in self.collectionFiles():
            # yield a file if we haven't heard of it yet of if it has been modified recently
            if f not in self.files or int(os.path.getmtime(f)) > self.files[f]:
                yield f

    def importFiles(self, files):
        for f in files:
            # new import task
            log.info('Import in %s collection: %s' % (self.name, f))
            if self.taskManager:
                importTask = ImportTask(self.graph, self.mediaTagger, f)
                self.taskManager.add(importTask)

            # TODO: is this correct to do this here or should we wait for the import task to succeed?
            self.files[f] = os.path.getmtime(f)

        # save newly imported files
        self.saveSettings()


    def update(self):
        log.info('Updating %s collection' % self.name)
        self.importFiles(self.modifiedFiles())

    def rescan(self):
        log.info('Rescanning %s collection' % self.name)
        self.importFiles(self.collectionFiles())

