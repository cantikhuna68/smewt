<%!
from collections import defaultdict
from smewt import SmewtUrl, Media
from smewt.media import Movie
from smewt.base.utils import pathToUrl, smewtDirectoryUrl, tolist
from smewt.base import SmewtException
import datetime, time
import os

import_dir = smewtDirectoryUrl('smewt', 'media')
flags_dir = smewtDirectoryUrl('smewt', 'media', 'common', 'images', 'flags')
%>

<%
movieName = movie.title
poster = pathToUrl(movie.loresImage)

def getAll(prop):
    return ', '.join(movie.get(prop) or [])

year = movie.get('year', '')
rating = movie.get('rating', '')
director = getAll('director')
writer = getAll('writer')
genres = getAll('genres')
englishSubsLink = SmewtUrl('action', 'getsubtitles', { 'type': 'movie', 'title': movieName, 'language': 'en' })
frenchSubsLink  = SmewtUrl('action', 'getsubtitles', { 'type': 'movie', 'title': movieName, 'language': 'fr' })
spanishSubsLink = SmewtUrl('action', 'getsubtitles', { 'type': 'movie', 'title': movieName, 'language': 'es' })

playLink = None
files = []
subtitles = []

languageFiles = defaultdict(lambda: [])

for media in tolist(movie.get('files')):
    files.append(media.filename)

for subtitle in tolist(movie.get('subtitles')):
    for subfile in tolist(subtitle.files):
        subtitleFilename = subfile.filename
        mediaFilename = [ filename for filename in files if subtitleFilename.startswith(os.path.splitext(filename)[0]) ]
        mediaFilename = mediaFilename[0] if mediaFilename else '' # FIXME: check len == 1 all the time

        languageFiles[subtitle.language] += [ (mediaFilename, subtitleFilename) ]


# prepare link for playing movie without subtitles
nfile = 1
args = {}
for f in sorted(files):
    args['filename%d' % nfile] = f
    nfile += 1

if args:
    playLink = SmewtUrl('action', 'play', args)


# prepare links for playing movie with subtitles
for lang, files in languageFiles.items():
    nfile = 1
    args = {}

    for (mediaFilename, subtitleFilename) in sorted(files):
        args['filename%d' % nfile] = mediaFilename
        args['subtitle%d' % nfile] = subtitleFilename
        nfile += 1

    subtitles.append( {'languageImage': flags_dir + '/%s.png' % (lang,),
                        'url': SmewtUrl('action', 'play', args)} )

subtitles.sort(key = lambda x: x['languageImage'])

def getComments(md):
    results = []

    for comment in tolist(md.get('comments')):
        results += [ (comment.author,
                      datetime.datetime.fromtimestamp(comment.date).ctime(),
                      comment.text) ]

    return sorted(results, key = lambda x: x[1])

comments = getComments(movie)

# FIXME: need to quote
qtitle = movie.title



%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
<title>single movie display</title>
<script type="text/javascript" src="${import_dir}/3rdparty/tabber.js"></script>
<link rel="stylesheet" href="${import_dir}/movie/movies.css" type="text/css">

  <script type="text/javascript" language="javascript" src="${import_dir}/3rdparty/dataTables/media/js/jquery.js"></script>

  <script type="text/javascript" charset="utf-8">
    function addComment(form, id, url) {
        mainWidget.addComment(url, 'Me', form[id].value);
    }
  </script>

</head>

<body>

<img src="${poster}" />

<div class="rightshifted">
  <h1>${movieName}</h1>

%if movieName != 'Unknown':
  %if playLink:
    <a href="${playLink}">Play Movie</a>
    %for s in subtitles:
       <a href="${s['url']}"><img src="${s['languageImage']}" /></a>
    %endfor
  %endif
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="${englishSubsLink}">Get missing English subtitles</a>
  <a href="${frenchSubsLink}">Get missing French subtitles</a>
  <a href="${spanishSubsLink}">Get missing Spanish subtitles</a>
%endif
</div>

%if movieName == 'Unknown':
<p>&nbsp;</p>
  %for f, url in [ (f, SmewtUrl('action', 'play', { 'filename1': f.filename })) for f in tolist(movie.get('files')) ]:

    <div class="singlefile"><a href="${url}"><i>${f['filename']}</i></a></div>
  %endfor


%else:

<div class="tabber">
  <div class="tabbertab">
    <h2>Overview</h2>
    <p><b>year:</b> ${year}</p>
    <p><b>rating:</b> ${rating}</p>
    <p><b>director:</b> ${director}</p>
    <p><b>writer:</b> ${writer}</p>
    <p><b>genres:</b> ${genres}</p>
    %if movie.plot:
      <p><b>plot:</b> ${movie.plot[0]}</p>
      %if len(movie.plot) > 1:
        <p><b>detailed plot:</b> ${movie.plot[1]}</p>
      %endif
    %endif
  </div>

  <div class="tabbertab">
    <h2>Cast</h2>
    %if 'cast' in movie:
      %for person_role in movie.cast:
        <p>${person_role}</p>
      %endfor
    %endif
    <p></p>
  </div>

  <div class="tabbertab">
    <h2>Comments</h2>
          %if comments:
            %for author, atime, comment in comments:
              <p>Comment by <b>${author}</b> at ${atime}:<br/>
              <div class="comment"><pre>${comment}</pre></div> </p>
            %endfor
          %else:
            <p><em>No Comments yet</em></p>
          %endif

          <form>
          <textarea rows="4" columns="80" name="text"></textarea>
          <button type="button" onClick="addComment(this.form, 'text', '${qtitle}')">Post new comment</button>
          </form>

  </div>

  <div class="tabbertab">
    <h2>Files</h2>

<%
allfiles = tolist(movie.get('files'))
for sub in tolist(movie.get('subtitles')):
    allfiles += tolist(sub.get('files'))

files = [ (f,
           SmewtUrl('action', 'play', { 'filename1': f.filename }),
           time.ctime(f.lastModified)) for f in allfiles ]

%>

    %for f, url, mtime in files:

      <div class="singlefile">
        <p><a href="${url}">${f.filename}</a></p>
        %for k, v in f.items():
          %if k == 'lastModified':
            <p><b>last scanned on</b>: ${mtime}</p>
          % elif k not in ['metadata', 'filename']:
            <p><b>${k}</b>: ${v}</p>
          %endif
        %endfor
      </div>
    %endfor


</div>
%endif

</body>
</html>
