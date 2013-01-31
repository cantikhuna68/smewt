#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Smewt - A smart collection manager
# Copyright (c) 2008-2012 Nicolas Wack <wackou@smewt.com>
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

import feedparser
import urllib2, re
import json
from PyQt4.QtCore import QSettings, QVariant
from smewt.base import SmewtException, EventServer
import logging

log = logging.getLogger(__name__)

DOWNLOAD_AGENT = 'MLDonkey'
import mldonkey as DownloadAgent


class FeedWatcher(object):
    def __init__(self):
        self.loadFeeds()
        self._ed2kRexp = re.compile('href="(?P<url>ed2k://\|file.*?)">')

    def feedListToQVariant(self, feedList):
        return QVariant([ QVariant([ QVariant(f['url']),
                                     QVariant(f['title']),
                                     QVariant([ QVariant(float(n)) for n in f['lastUpdate'] ]),
                                     QVariant(f['lastTitle']),
                                     QVariant(json.dumps(f['entries']))
                                     ]) for f in feedList ])

    def variantToFeedList(self, v):
        result = []
        for f in v.toList():
            feed = {}
            feed['url'] = str(f.toList()[0].toString())
            feed['title'] = str(f.toList()[1].toString())
            feed['lastUpdate'] = [ n.toInt()[0] for n in f.toList()[2].toList() ]
            feed['lastTitle'] = unicode(f.toList()[3].toString())
            try:
                feed['entries'] = json.loads(str(f.toList()[4].toString()))
            except:
                feed['entries'] = []
            result.append(feed)
        return result

    def loadFeeds(self):
        # TODO: store inside graph db instead of Qt settings
        self.feedList = self.variantToFeedList(QSettings().value('feeds'))

    def saveFeeds(self):
        # TODO: store inside graph db instead of Qt settings
        QSettings().setValue('feeds', self.feedListToQVariant(self.feedList))

    def addFeed(self, url, lastUpdate = None):
        """Example:
        url = 'http://tvu.org.ru/rss.php?se_id=19934' # South Park season 12
        lastUpdate = [2008, 10, 30, 2, 47, 39, 3, 304, 0]
        addFeed(url, lastUpdate)

        if lastUpdate is not specified, it will assume all episodes have already been downloaded"""

        url = str(url)
        if url in [ f['url'] for f in self.feedList ]:
            return

        feed = { 'url': url }
        self.updateFeed(feed)
        if not lastUpdate:
            lastUpdate = feed['entries'][0]['updated']
        self.setLastUpdate(feed, lastUpdate)

        self.feedList.append(feed)
        self.saveFeeds()
        log.info('Subscribed to feed: %s' % url)

    def removeFeed(self, url):
        for f in self.feedList:
            if f['url'] == url:
                self.feedList.remove(f)
                self.saveFeeds()
                log.info('Unsubscribed from feed: %s' % url)

    def updateFeed(self, feed):
        try:
            pfeed = feedparser.parse(feed['url'])
            entries = [ { 'title': entry.title,
                          'updated': list(entry.updated_parsed) } for entry in pfeed.entries ]

            feed.update({ 'title': pfeed.channel.title,
                          'entries': entries })

            self.saveFeeds()
            log.info('Updated info for feed: %s' % feed['url'])

            return pfeed
        except:
            raise SmewtException('Invalid feed!')

    def updateFeedUrl(self, url):
        for f in self.feedList:
            if f['url'] == url:
                self.updateFeed(f)

    def setLastUpdateUrlIndex(self, url, index):
        for feed in self.feedList:
            if feed['url'] == url:
                lastUpdate = feed['entries'][index]['updated']
                self.setLastUpdate(feed, lastUpdate)

    def setLastUpdate(self, feed, lastUpdate):
        feed['lastUpdate'] = lastUpdate
        # also save last ep title:
        for f in feed['entries']:
            if lastUpdate == f['updated']:
                feed['lastTitle'] = f['title']
                break
        self.saveFeeds()


    def amuleDownload(self, ed2kLink):
        from amulecommand import AmuleCommand
        return AmuleCommand().download(ed2kLink)

    def mldonkeyDownload(self, ed2kLink):
        import mldonkey
        return mldonkey.download(ed2kLink)

    def downloadNewEpisodes(self, feed):
        EventServer.publish('Checking new episodes for: %s' % feed['title'])
        f = self.updateFeed(feed)
        lastUpdate = feed['lastUpdate']

        for ep in f.entries[::-1]:
            if list(ep.updated_parsed) > feed['lastUpdate']:
                EventServer.publish('Found new episode: %s' % ep.title)
                episodeHtml = urllib2.urlopen(ep.id).read()
                ed2kLink = self._ed2kRexp.search(episodeHtml).groups()[0]
                EventServer.publish('Sending link %s to %s...' %
                                    (ed2kLink, DOWNLOAD_AGENT))
                try:
                    ok, msg = DownloadAgent.download(ed2kLink)
                    if not ok:
                        raise RuntimeError('Could not send link to %r: %s' %
                                           (DOWNLOAD_AGENT, msg))

                    EventServer.publish('Successfully sent %s to %s!' %
                                        (ed2kLink.split('|')[2], DOWNLOAD_AGENT))
                    if list(ep.updated_parsed) > lastUpdate:
                        lastUpdate = list(ep.updated_parsed)
                except Exception as e:
                    log.error('Error while sending to %s: %s' % (DOWNLOAD_AGENT, e))
                    EventServer.publish('Error while sending to %s. %s. Will try again next time...' %
                                        (DOWNLOAD_AGENT, e))

        if lastUpdate == feed['lastUpdate']:
            EventServer.publish('No new episodes...')
        else:
            self.setLastUpdate(feed, lastUpdate)

    def checkAllFeeds(self):
        for feed in self.feedList:
            self.downloadNewEpisodes(feed)

        # write back feed list with latest updates
        self.saveFeeds()