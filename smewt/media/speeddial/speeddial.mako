<html>
<head>
  <title>All movies view</title>

  <style type="text/css">

  td.center {
    text-align: center;
  }

  td {
    padding: 24px;
    padding-bottom: 18px;
    background-color: #BBBBBB;
  }

  #header {
    text-align: center;
    font: bold 24px Verdana, sans-serif;
    color: #333333;
  }

  p {
    text-decoration: none;
    font: bold 20px Verdana, sans-serif;
    color: #448;
  }

  body {
    background-color: #EEEEEE;
  }


  </style>

</head>

<%!
from smewt.base.utils import smewtDirectoryUrl, smewtUserDirectoryUrl
smewt_dir = smewtDirectoryUrl('smewt', 'media', 'speeddial')
import_dir = smewtUserDirectoryUrl('speeddial')
%>

<body>
  <div id="header">Smewt Dial</div>

    <div id="speeddial"><form>

    <table id="layout" class="display" align="center" cellspacing="24">
      <tbody>
        <tr>
          <td class="center"><a href="smewt://media/series/all">
                             <img src="${import_dir}/allseries.png" width="200" /></a>
                             <p>Series Posters</p></td>

          <td class="center"><a href="smewt://media/movie/all">
                            <img src="${import_dir}/allmovies.png" width="200" /></a>
                            <p>Movie Posters</p></td>

          <td class="center"><a href="smewt://media/movie/recent">
                             <img src="${import_dir}/recentmovies.png" width="200" /></a>
                             <p>Recently Watched Movies</p></td>

        </tr>
        <tr>
          <td class="center"><a href="smewt://media/series/suggestions">
                             <img src="${import_dir}/episodesuggestions.png" width="200" /></a>
                             <p>Episode Suggestions</p></td>

          <td class="center"><a href="smewt://media/movie/spreadsheet">
                             <img src="${import_dir}/moviespreadsheet.png" width="200" /></a>
                             <p>All Movies</p></td>

          <!--
          <td class="center"><a href="smewt://feedwatcher">
                             <img src="${import_dir}/feedwatcher_200x150.png" width="200" /></a>
                             <p>Feed Watcher</p></td>
           -->
        </tr>

      </tbody>
    </table>
