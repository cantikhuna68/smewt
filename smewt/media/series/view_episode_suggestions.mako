<%inherit file="base_episode.mako"/>

<%!
from smewt import SmewtUrl
from smewt.base.utils import tolist, pathToUrl
from smewt.base.textutils import toUtf8
from itertools import groupby
import datetime
%>

<%
episodes = context['episodes']

# map of series to list of episodes
suggest = {}

episodeCount = 3

# first find the last viewed episode for each season
episodes = sorted(episodes, key = lambda ep: ep.series.title)

for serieName, eps in groupby(episodes, lambda ep: ep.series.title):
    eps = list(eps)
    lastViewed = max(eps, key = lambda ep: ep.lastViewed)

    # then look if we have a more recent one which we haven't watched yet
    s = []
    for ep in tolist(lastViewed.series.episodes):
        if 'title' in ep and (ep.season, ep.episodeNumber) >= (lastViewed.season, lastViewed.episodeNumber):
            s.append(ep)


    # find only more recent episode to watch
    if s:
        keep = sorted(s, key = lambda ep: (ep.season, ep.episodeNumber))[:episodeCount]
        suggest[keep[0].series] = keep


# sort our suggestions to show the last scanned ones first
suggest = sorted(suggest.items(), key = lambda eps: -tolist(eps[1][0].files)[0].lastModified)

from smewt.base.utils import smewtDirectoryUrl
import_dir = smewtDirectoryUrl('smewt', 'media')

%>

<div class="container-fluid">

  ${parent.make_header('EPISODES SUGGESTIONS')}

    %if suggest:
        %for s, eps in suggest:
            <div class="row-fluid"><div class="span12">
            <%
              url = SmewtUrl('media', 'series/single', { 'title': s.title })
              poster = pathToUrl(s.get('loresImage'))
            %>
            ${parent.make_title_box(poster, s.title, url)}
            </div></div>

            %for ep in eps:
                <div class="row-fluid"><div class="span12">
                ${parent.make_episode_box(ep)}
                </div></div>
            %endfor
      %endfor
    %else:
      <p>No episode suggestions are available at this moment.</p>

      <p>When you start watching series, this view will show you the most recent episodes that you haven't seen yet, sorted by series .</p>
    %endif
    </div>
    </div>

</div>
</div>
