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

from smewt.solvers.solver import Solver
import copy


class NaiveSolver(Solver):
    def __init__(self):
        super(NaiveSolver, self).__init__()

    def solve(self, query):
        self.checkValid(query)

        results = sorted(query.metadata, cmp = lambda x, y: x.confidence > y.confidence)
        result = copy.copy(results[0])

        #resultMediaObject = copy.copy(mediaObjects[0])

        for md in results[1:]:
            merge = True
            for k, v in md.properties.items():
                #print 'Solver: Checking property ''%s'' ::: ''%s'' (%r) -- ''%s'' (%r)' % (k, v, mediaObject.confidence[k], resultMediaObject[k], resultMediaObject.confidence[k])
                #if mediaObject.confidence.get(k, 0.0) > resultMediaObject.confidence.get(k, 0.0):
                #if md.confidence[k] > resultMediaObject.confidence[k]:
                #    resultMediaObject[k] = v
                #    resultMediaObject.confidence[k] = mediaObject.confidence[k]
                if result[k] and v and result[k] != v:
                    merge = False
            # FIXME: big hack
            if list(result.getUniqueKey()).count(None) > 0 and md.confidence < 0.6:
                merge = False
            if merge:
                for k in md.properties:
                    result[k] = md[k]

        self.found(query, result)

