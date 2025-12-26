# coding=utf-8

import time
import os
import json
import os, string, hashlib, base64, re, plistlib, unicodedata
from collections import defaultdict
from io import open

# Ximalaya APIs
XIMALAYA_SEARCH_BASE = 'https://www.ximalaya.com/revision/search'
XIMALAYA_TRACK_URL = 'http://mobwsa.ximalaya.com/mobile/playlist/album/page?albumId='
XIMALAYA_ARTIST_ALBUM = 'https://www.ximalaya.com/revision/user/pub?uid='
XIMALAYA_ARTIST_URL = 'https://www.ximalaya.com/revision/user/basic?uid='
XIMALAYA_ALBUM_INFO = 'https://www.ximalaya.com/revision/album/v1/simple?albumId='

# Tunables
ARTIST_MATCH_LIMIT = 9
ARTIST_MATCH_MIN_SCORE = 85
ARTIST_MANUAL_MATCH_LIMIT = 120
ARTIST_SEARCH_PAGE_SIZE = 30
ARTIST_ALBUMS_MATCH_LIMIT = 3
ARTIST_ALBUMS_LIMIT = 50
ARTIST_MIN_LISTENER_THRESHOLD = 250
ARTIST_MATCH_GOOD_SCORE = 90
ALBUM_MATCH_LIMIT = 8
ALBUM_MATCH_MIN_SCORE = 75
ALBUM_MATCH_GOOD_SCORE = 92
ALBUM_TRACK_BONUS_MATCH_LIMIT = 5
QUERY_SLEEP_TIME = 0.1

# Advanced tunables
NAME_DISTANCE_THRESHOLD = 2
ARTIST_INITIAL_SCORE = 90
ARTIST_ALBUM_BONUS_INCREMENT = 3
ARTIST_ALBUM_MAX_BONUS = 15
ARTIST_MAX_DIST_PENALTY = 40
ALBUM_INITIAL_SCORE = 92
ALBUM_NAME_DIST_COEFFICIENT = 5
ALBUM_TRACK_BONUS_INCREMENT = 3
ALBUM_TRACK_MAX_BONUS = 20
ALBUM_TRACK_BONUS_MAX_ARTIST_DSIT = 2
ALBUM_NUM_TRACKS_BONUS = 1

RE_STRIP_PARENS = Regex('\([^)]*\)')

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

def Start():
  HTTP.CacheTime = CACHE_1WEEK

def multi_get_letter(str_input): 
  if isinstance(str_input, unicode): 
    unicode_str = str_input 
  else: 
    try: 
      unicode_str = str_input.decode('utf8') 
    except: 
      try: 
        unicode_str = str_input.decode('gbk') 
      except: 
        return
  return single_get_first(unicode_str)

def single_get_first(unicode1): 
  str1 = unicode1.encode('gbk') 
  try:     
    ord(str1) 
    return str1 
  except: 
    asc = ord(str1[0]) * 256 + ord(str1[1]) - 65536
    if asc >= -20319 and asc <= -20284: return 'a'
    if asc >= -20283 and asc <= -19776: return 'b'
    if asc >= -19775 and asc <= -19219: return 'c'
    if asc >= -19218 and asc <= -18711: return 'd'
    if asc >= -18710 and asc <= -18527: return 'e'
    if asc >= -18526 and asc <= -18240: return 'f'
    if asc >= -18239 and asc <= -17923: return 'g'
    if asc >= -17922 and asc <= -17418: return 'h'
    if asc >= -17417 and asc <= -16475: return 'j'
    if asc >= -16474 and asc <= -16213: return 'k'
    if asc >= -16212 and asc <= -15641: return 'l'
    if asc >= -15640 and asc <= -15166: return 'm'
    if asc >= -15165 and asc <= -14923: return 'n'
    if asc >= -14922 and asc <= -14915: return 'o'
    if asc >= -14914 and asc <= -14631: return 'p'
    if asc >= -14630 and asc <= -14150: return 'q'
    if asc >= -14149 and asc <= -14091: return 'r'
    if asc >= -14090 and asc <= -13119: return 's'
    if asc >= -13118 and asc <= -12839: return 't'
    if asc >= -12838 and asc <= -12557: return 'w'
    if asc >= -12556 and asc <= -11848: return 'x'
    if asc >= -11847 and asc <= -11056: return 'y'
    if asc >= -11055 and asc <= -10247: return 'z'
    return ''

def pinyin(str_input): 
  b = ''
  if isinstance(str_input, unicode): 
    unicode_str = str_input 
  else: 
    try: 
      unicode_str = str_input.decode('utf8')
    except: 
      try: 
        unicode_str = str_input.decode('gbk')
      except: 
        return  
  for i in range(len(unicode_str)):
    b=b+single_get_first(unicode_str[i])
  return b.upper()

def score_artists(artists, media_artist, media_albums, lang, artist_results):
  for i, artist in enumerate(artists):
    id = str(artist['uid'])
    dist = int(ARTIST_MAX_DIST_PENALTY - ARTIST_MAX_DIST_PENALTY * LevenshteinRatio(artist['nickname'].lower(), media_artist.lower()))
    if artist['nickname'].lower() == media_artist.lower():
      dist = dist - 1
    if i < ARTIST_ALBUMS_MATCH_LIMIT:
      bonus = get_album_bonus(media_albums, artist_id=id)
    else:
      bonus = 0
    score = ARTIST_INITIAL_SCORE + bonus - dist
    name = artist['nickname']
    if score >= ARTIST_MATCH_MIN_SCORE:
      artist_results.append(MetadataSearchResult(id=id, name=name, lang=lang, score=score))
    else:
      Log('Skipping artist, didn\'t meet minimum score.')
    artist_results.sort(key=lambda r: r.score, reverse=True)    

def get_album_bonus(media_albums, artist_id):
  bonus = 0
  albums = GetAlbumsByArtist(artist_id, albums=[], limit=ARTIST_ALBUMS_LIMIT)
  try:
    for a in media_albums:    
      media_album = a.lower()
      for album in albums:
        if Util.LevenshteinDistance(media_album,album['title'].lower()) <= NAME_DISTANCE_THRESHOLD:
          bonus += ARTIST_ALBUM_BONUS_INCREMENT
        elif Util.LevenshteinDistance(media_album,RE_STRIP_PARENS.sub('',album['title'].lower())) <= NAME_DISTANCE_THRESHOLD:
          bonus += ARTIST_ALBUM_BONUS_INCREMENT
        if bonus >= ARTIST_ALBUM_MAX_BONUS:
          break
  except Exception, e:
    Log('Error applying album bonus: ' + str(e))
  return bonus

class Ximalaya(Agent.Artist):
  name = 'Ximalaya'
  languages = [Locale.Language.Chinese]
  
  def score_by_albums(self, media, lang, local_albums_name, albums, manual=False):
    res = []
    matches = []
    for j, album in enumerate(albums):
      try:
        # Field mapping for search results
        name = album.get('title', '')
        # Some search results use 'id', some 'albumId'.
        id = str(album.get('id', album.get('albumId', '')))
        
        # Search API returns 'nickname' for artist name
        artist_name = album.get('nickname', '')
        artist_id = str(album.get('uid', ''))

        score = ALBUM_INITIAL_SCORE - j * 10
        res.append({'id': artist_id, 'name': artist_name, 'lang':lang, 'score':score, 'album_id':id, 'album_name':name, 'year':1990})
      except:
        Log('Error scoring album.')

    if res:
      res = sorted(res, key=lambda k: k['score'], reverse=True)
      for i, result in enumerate(res):
        if i < ALBUM_TRACK_BONUS_MATCH_LIMIT:
          bonus = self.get_track_bonus(media, result['album_id'], lang)
          res[i]['score'] = res[i]['score'] + bonus
        if res[i]['score'] >= ALBUM_MATCH_MIN_SCORE or manual:
          matches.append(res[i])
        else:
          break

    if matches:
      return sorted(matches, key=lambda k: k['score'], reverse=True)
    else:
      return matches
    
  def get_track_bonus(self, media, album_id, lang):
    track_num, tracks = GetTracks(media.id, str(album_id), lang)
    bonus = 0
    # Guard against empty tracks
    if not tracks:
        return 0

    for i, t in enumerate(media.children[0].children):
      media_track = t.title.lower()
      for j, track in enumerate(tracks):
        # API track title key is 'title'
        track_title = track.get('title', '').lower()
        if Util.LevenshteinDistance(track_title, media_track) < 5:
          bonus += ALBUM_TRACK_BONUS_INCREMENT
      if i > 10:
        break

    if abs(len(media.children) - int(track_num)) < 6:
      bonus += 5
    
    if bonus >= ALBUM_TRACK_MAX_BONUS:
      bonus = ALBUM_TRACK_MAX_BONUS

    return bonus

  def search(self, results, media, lang, manual):
    media_albums = [a.title for a in media.children]
    
    if media.artist == '[Unknown Artist]':
      artist_byalbums = self.score_by_albums(media, lang, media_albums[0], SearchAlbums(media_albums[0].lower(), ALBUM_MATCH_LIMIT), manual=manual)
      for artist in artist_byalbums:
        results.Append(MetadataSearchResult(id = str(artist['id']), name= artist['name'], lang  = lang, score = int(artist['score'])))
      return
    
    if media.artist == 'Various Artists':
      results.Append(MetadataSearchResult(id = 'Various%20Artists', name= 'Various Artists', thumb = VARIOUS_ARTISTS_POSTER, lang  = lang, score = 100))
      return

    Log('Search Artist: ' + media.artist)
    artist_results = []
    # Search for artist
    artists = SearchArtists(media.artist, ARTIST_MATCH_LIMIT)
    
    if artists:
      score_artists(artists, media.artist, media_albums, lang, artist_results)
      if artist_results :
        for artist in artist_results:
          results.Append(artist)
      else:
        artist_byalbums = self.score_by_albums(media, lang, media_albums[0], SearchAlbums(media_albums[0].lower(), ALBUM_MATCH_LIMIT), manual=manual)
        for artist in artist_byalbums:
          results.Append(MetadataSearchResult(id = str(artist['id']), name= artist['name'], lang  = lang, score = int(artist['score'])))
        return
    else:
      artist_byalbums = self.score_by_albums(media, lang, media_albums[0], SearchAlbums(media_albums[0].lower(), ALBUM_MATCH_LIMIT), manual=manual)
      for artist in artist_byalbums:
        results.Append(MetadataSearchResult(id = str(artist['id']), name= artist['name'], lang  = lang, score = int(artist['score'])))
      return

  def update(self, metadata, media, lang):
    artist = GetArtist(metadata.id, lang)
    try:
      metadata.title = artist['nickName']
      metadata.title_sort = pinyin(metadata.title)
    except:
      pass
    try:
      metadata.summary = artist['personalSignature'].strip()
    except:
      pass
    try:
      if artist.get('nickName') == 'Various Artists':
          pass
      else:       
          cover = artist.get('cover', '')
          if cover and not cover.startswith('http'):
              cover = 'https:' + cover
          metadata.posters[cover] = Proxy.Media(HTTP.Request(cover))
    except:
        Log('Couldn\'t add artwork for artist.')

class XimalayaAgent(Agent.Album):
  name = 'Ximalaya'
  languages = [Locale.Language.Chinese]
  accepts_from = ['com.plexapp.agents.localmedia','com.plexapp.agents.lyricfind']
  
  def search(self, results, media, lang, manual):
    albums = []
    if manual:
      try:
        media.title = media.name
      except:
        pass
    
    found_good_match = False

    # No artist info
    if media.parent_metadata.id is None:
      albums = self.score_by_albums(media, lang, SearchAlbums(media.name.lower(), ALBUM_MATCH_LIMIT), manual=manual) + albums
      seen = {}
      deduped = []
      for album in albums:
        if album['id'] in seen:
          continue
        seen[album['id']] = True
        deduped.append(album)
      albums = deduped
      albums = albums[:10]
      for i,album in enumerate(albums):
        if album['score'] > 0:
          score = album['score']
          if score >= 100:
            score = 99 - i
          results.Append(MetadataSearchResult(id = str(album['id']), name = album['name'], lang = album['lang'], score = str(score)))
      return

    if media.parent_metadata.id == '[Unknown Album]':
      return 

    if media.parent_metadata.id != 'Various%20Artists':
      if not manual:
        albums = self.score_albums(media, lang, GetAlbumsByArtist(media.parent_metadata.id, albums=[]))
        if albums and albums[0]['score'] >= ALBUM_MATCH_GOOD_SCORE:
          found_good_match = True

      if manual:
        albums = self.score_albums(media, lang, GetAlbumsByArtist(media.parent_metadata.id, albums=[]), manual=manual)
        if albums and albums[0]['score'] >= ALBUM_MATCH_GOOD_SCORE:
          found_good_match = True

    if not found_good_match or not albums:
      albums = self.score_by_albums(media, lang, SearchAlbums(media.title.lower(), ALBUM_MATCH_LIMIT), manual=manual) + albums
      
    seen = {}
    deduped = []
    for album in albums:
      if album['id'] in seen:
        continue
      seen[album['id']] = True
      deduped.append(album)
    albums = deduped
    albums = albums[:10]

    for i,album in enumerate(albums):
        if album['score'] > 0:
          score = album['score']
          if score >= 100:
            score = 99 - i
          results.Append(MetadataSearchResult(id = str(album['id']), name = album['name'], lang = album['lang'], score = str(score)))
    return

  def score_by_albums(self, media, lang, albums, manual=False):
    res = []
    matches = []
    for j, album in enumerate(albums):
        name = album.get('title', '')
        # Search API returns 'id'
        id = str(album.get('id', album.get('albumId', '')))
        score = ALBUM_INITIAL_SCORE - j * 10 
        res.append({'id':id, 'name':name, 'lang':lang, 'score':score})

    if res:
      res = sorted(res, key=lambda k: k['score'], reverse=True)
      for i, result in enumerate(res):
        if i < ALBUM_TRACK_BONUS_MATCH_LIMIT:
          bonus = self.get_track_bonus(media, result['id'], lang)
          res[i]['score'] = res[i]['score'] + bonus
        if res[i]['score'] >= ALBUM_MATCH_MIN_SCORE or manual:
          matches.append(res[i])
        else:
          break

    if matches:
      return sorted(matches, key=lambda k: k['score'], reverse=True)
    else:
      return matches
    
  def score_albums(self, media, lang, albums, manual=False):
    res = []
    matches = []
    for album in albums:
      try:
        name = album['title']
        id =  str(album.get('albumId', album.get('id', '')))
        dist = Util.LevenshteinDistance(name.lower(), media.title.lower()) * ALBUM_NAME_DIST_COEFFICIENT
        artist_dist = 100
        
        # Adaptation for different artist key names
        anchor_name = album.get('anchorNickName', album.get('nickname', ''))
        
        if Util.LevenshteinDistance(anchor_name.lower(), String.Unquote(media.parent_metadata.title).lower()) < artist_dist :
            artist_dist = Util.LevenshteinDistance(anchor_name.lower(), String.Unquote(media.parent_metadata.title).lower())
        
        if artist_dist > ALBUM_TRACK_BONUS_MAX_ARTIST_DSIT:
          artist_dist = 1000
        
        score = ALBUM_INITIAL_SCORE - dist - artist_dist
        res.append({'id':id, 'name':name, 'lang':lang, 'score':score})
      except:
        Log('Error scoring album.')

    if res:
      res = sorted(res, key=lambda k: k['score'], reverse=True)
      for i, result in enumerate(res):
        if i < ALBUM_TRACK_BONUS_MATCH_LIMIT:
          bonus = self.get_track_bonus(media, result['id'], lang)
          res[i]['score'] = res[i]['score'] + bonus
        if res[i]['score'] >= ALBUM_MATCH_MIN_SCORE or manual:
          matches.append(res[i])
        else:
          break

    if matches:
      return sorted(matches, key=lambda k: k['score'], reverse=True)
    else:
      return matches
  
  def get_track_bonus(self, media, album_id, lang):
    track_num, tracks = GetTracks(media.parent_metadata.id, str(album_id), lang)
    bonus = 0
    try:
      for i, t in enumerate(media.children):
        media_track = t.title.lower()
        for j, track in enumerate(tracks):
          if Util.LevenshteinDistance(track.get('title', '').lower(), media_track) <  NAME_DISTANCE_THRESHOLD:
            bonus += ALBUM_TRACK_BONUS_INCREMENT
        if i > 15:
          break

      if abs(len(media.children) - int(track_num)) < 6:
        bonus += 5
      
      if bonus >= ALBUM_TRACK_MAX_BONUS:
        bonus = ALBUM_TRACK_MAX_BONUS

    except:
      Log('Didn\'t find any usable tracks in search results, not applying track bonus.')

    return bonus
 
  def update(self, metadata, media, lang):
    album = GetAlbum(metadata.id, lang)
    if not album:
      return

    try:
        metadata.title = album['albumTitle']
    except:
        pass
    
    try:
      cover = album.get('cover', '')
      if cover:
          if not cover.startswith('http'):
              cover = 'https:' + cover
          valid_keys = cover
          metadata.posters[valid_keys] = Proxy.Media(HTTP.Request(valid_keys))
    except:
      Log('Couldn\'t add artwork for album.')

    try:
      # Try timestamp first, then string
      if 'createDate' in album:
          metadata.originally_available_at = Datetime.ParseDate(album['createDate'])
      elif 'publishTime' in album:
          metadata.originally_available_at = Datetime.ParseDate(time.strftime("%Y-%m-%d", time.localtime(int(int(album['publishTime'])/1000))))
    except:
      Log('Couldn\'t add release date to album.')
      
    try:
      detailRichIntro = album.get('detailRichIntro', album.get('intro', ''))
      # Clean rich text if necessary or just use intro
      if '<' in detailRichIntro:
          html_elem = HTML.ElementFromString(detailRichIntro)
          summary = ''
          for i in html_elem.xpath('//p'):
              summary = summary + ''.join(i.xpath('.//text()')) + '\n'
          metadata.summary = summary
      else:
          metadata.summary = detailRichIntro
      
      metadata.studio = '喜马拉雅'
    except:
      Log("Error parsing summary")

    metadata.genres.clear()
    try:
        tags = album.get('tags', [])
        if isinstance(tags, str):
            tags = tags.split(',')
        for genre in Listify(tags):
          metadata.genres.add(genre.capitalize())
    except:
        Log('Couldn\'t add genre tags to album.')

    for index in media.tracks:
      key = media.tracks[index].guid or int(index)
      metadata.tracks[key].original_title = media.parentTitle

    most_popular_tracks = {}
    try:
      top_tracks = GetArtistTopTracks(metadata.id.split('/')[0], lang)
      for track in top_tracks:
        most_popular_tracks[track['name']] = int(track['pop'])
    except:
      pass

def DownlodeLyric(trackid):
  url = LYRIC_URL_WANGYI + str(trackid) + '&lv=1&tv=1'
  try: 
    response = GetJSON(url)
  except:
    Log('Error retrieving lrc search results.')
  return response 
  
def SearchArtists(artist, limit=10):
  artists = []
  if not artist:
    return artists
  try:
    a = artist.lower().encode('utf-8')
  except:
    a = artist.lower()
  
  # Search API
  url = XIMALAYA_SEARCH_BASE + '?core=user&kw=' + String.Quote(a) + '&page=1&rows=' + str(limit)
  
  try: 
    response = GetJSON(url)
    # Parse results
    if 'data' in response and 'result' in response['data']:
        docs = response['data']['result']['response']['docs']
        artists = Listify(docs)
        # Add 'nickname' if missing from 'title' to standardize
        for art in artists:
            if 'nickname' not in art and 'title' in art:
                art['nickname'] = art['title']
  except:
    Log('Error retrieving artist search results.')
    return artists
  return artists

def SearchAlbums(album, limit=10, legacy=False):
  albums = []
  if not album:
    return albums
  try:
    a = album.lower().encode('utf-8')
  except:
    a = album.lower()
  
  # Search API
  url = XIMALAYA_SEARCH_BASE + '?core=album&kw=' + String.Quote(a) + '&page=1&rows=' + str(limit)
  
  try:
    response = GetJSON(url)
    if 'data' in response and 'result' in response['data']:
        docs = response['data']['result']['response']['docs']
        albums = Listify(docs)
    elif response.has_key('error'):
      Log('Search error: ' + response['message'])
  except:
    Log('Error retrieving album search results.')

  return albums

def GetAlbumsByArtist(artist_id, limit=ARTIST_ALBUMS_LIMIT*4, albums=[], legacy=True):
  # Legacy API usage
  url = XIMALAYA_ARTIST_ALBUM + artist_id
  response = GetJSON(url)
  try:
    albums.extend(Listify(response['data']['albumList']))
  except:
    pass
  return albums

def GetArtist(id, lang='en'):
  url = XIMALAYA_ARTIST_URL + id
  try:
    artist_results = GetJSON(url)
    if artist_results.has_key('error'):
      return {}
    return artist_results['data']
  except:
    return {}

def GetAlbum(album_id, lang='en'):
  url = XIMALAYA_ALBUM_INFO + album_id
  try:
    album_results = GetJSON(url)
    if album_results.has_key('error'):
      return {}
    return album_results['data']['albumPageMainInfo']
  except:
    return {}

def GetTracks(artist_id, album_id, lang='en'):
  # Mobile API
  # Note: API requires pageId, assumes page 1.
  url = XIMALAYA_TRACK_URL + album_id + '&pageId=1'
  try:
    tracks_result = GetJSON(url)
    # Parse total count and list
    total = 0
    track_list = []
    
    if 'totalCount' in tracks_result:
        total = tracks_result['totalCount']
        track_list = Listify(tracks_result.get('list', []))
    elif 'data' in tracks_result:
        total = tracks_result['data'].get('totalCount', 0)
        track_list = Listify(tracks_result['data'].get('list', []))
        
    return total, track_list
  except:
    Log('Error retrieving tracks.')
    return '0',[]

def GetArtistTopTracks(artist_id, lang='en'):
  result = []
  url = ARTIST_URL_WANGYI + artist_id.lower()
  top_tracks_result = GetJSON(url)
  try:
    for songs in top_tracks_result['hotSongs']:
      if int(songs['pop']) >= 95 :
        new_results = songs
        result.append(new_results)
  except:
    pass
  return result

def GetArtistSimilar(artist_id, lang='en'):
  return []

def GetJSON(url, sleep_time=QUERY_SLEEP_TIME, cache_time=CACHE_1MONTH):
  d = None
  try:
    d = JSON.ObjectFromURL(url, sleep=sleep_time, cacheTime=cache_time, headers=headers)
    if isinstance(d, dict):
      return d
  except:
    Log('Error fetching JSON.')
    return None

def LevenshteinRatio(first, second):
  return 1 - (Util.LevenshteinDistance(first, second) / float(max(len(first), len(second))))

def NormalizeArtist(name):
  return Core.messaging.call_external_function('com.plexapp.agents.plexmusic', 'MessageKit:NormalizeArtist', kwargs = dict(artist=name))

def Listify(obj):
  if isinstance(obj, list):
    return obj
  else:
    return [obj]

def Dictify(obj, key=''):
  if isinstance(obj, dict):
    return obj
  else:
    return {key:obj}
