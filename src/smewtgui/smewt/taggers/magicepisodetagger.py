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

from smewt.taggers.tagger import Tagger
from smewt.guessers import *
from smewt.solvers import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import copy
import sys
import re
from os.path import join, split, basename

from smewt import Collection
from smewt.media.series import Episode

class MagicEpisodeTagger(Tagger):
    def __init__(self):
        super(MagicEpisodeTagger, self).__init__()
        self.guesserIndex = 0
        self.guessers = [episodefilename.EpisodeFilename(), epguides.EpGuides()]
        self.solver = naivesolver.NaiveSolver()

        # Connect each guesser to the next
        for index, guesser in enumerate(self.guessers[:-1]):
            self.connect(guesser, SIGNAL('finished'), self.guessers[index+1].start)

        # Connect the last guesser to the solver
        self.connect(self.guessers[-1], SIGNAL('finished'), self.solver.start)

        # Connect the solver to the solved slot
        self.connect(self.solver, SIGNAL('finished'), self.solved)

    def solved(self, taggedMediaObject):
        self.emit(SIGNAL('tagFinished'), taggedMediaObject)

    def tag(self, mediaObject):
        if mediaObject.type() == 'video':
            if mediaObject.filename:
                query = Collection()
                query.media = [ mediaObject ]
                self.guessers[0].start(query)
                return
            else:
                print 'Tagger: filename hasn\'t been set on Media object.'
        else:
            print 'Tagger: Not a video media.  Cannot tag.'

        return super(MagicEpisodeTagger, self).tag(mediaObject)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tagger = MagicEpisodeTagger()
    mediaObject = EpisodeObject.fromDict({'filename': sys.argv[1]})

    def printResults(tagged):
        print tagged

    app.connect(tagger, SIGNAL('tagFinished'), printResults)

    tagger.tag(mediaObject)

    app.exec_()
