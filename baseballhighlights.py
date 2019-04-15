# -*- coding: utf-8 -*-
# Module: default
# Author: Peter Helbing
# Created on: 15.04.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import print_function

import datetime
import dateutil.parser
import json
import urllib

FANART_SIZE = 1920
THUMB_SIZE = 960
ICON_SIZE = 640


def get_image_url(base_json, max_size):
    try:
        cuts_json = base_json["image"]["cuts"]
    except KeyError:
        cuts_json = None
    if cuts_json is not None:
        try:
            return next(c["src"] for c in cuts_json if c["width"] <= max_size)
        except StopIteration:
            return None
    else:
        return None


def convert_duration(duration_string):
    time = dateutil.parser.parse(duration_string).time()
    td = datetime.timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
    return int(td.total_seconds())


class Highlight:
    # members:
    # - url
    # - title
    # - fanart
    # - thumb
    # - icon
    # - contentType
    # - description
    # - description_short
    # - duration
    def __init__(self, highlight_json):
        self.url = None
        try:
            for playback in highlight_json["playbacks"]:
                if playback["name"] == "mp4Avc":
                    self.url = playback["url"]
        except KeyError:
            return

        self.title = highlight_json["title"]
        self.description = highlight_json["description"]
        self.description_short = highlight_json["blurb"]
        self.duration = convert_duration(highlight_json["duration"])

        self.fanart = get_image_url(highlight_json, FANART_SIZE)
        self.thumb = get_image_url(highlight_json, THUMB_SIZE)
        self.icon = get_image_url(highlight_json, ICON_SIZE)

        self.contentType = "H"
        try:
            content_type_json = next(item["value"] for item in highlight_json["keywordsDisplay"]
                                     if item["type"] == "mlbtax")
            convert = {"condensed_game": "C", "mlb_recap": "R"}
            if content_type_json in convert.keys():
                self.contentType = convert[content_type_json]
        except StopIteration:
            pass

    def __unicode__(self):
        return u"{0}: {1}\nurl: {2}\nthumb: {3}".format(self.contentType, self.title, self.url, self.thumb)

    def __str__(self):
        return unicode(self).encode('utf-8')


class Game:
    def __init__(self, gameid):
        # members:
        # - gameid
        # - title
        # - title_short
        # - fanart
        # - thumb
        # - icon
        # - description
        # - description_short
        # - highlights
        self.gameId = gameid

        game_query_url = "https://statsapi.mlb.com/api/v1/game/{0}/feed/live".format(gameid)
        response = urllib.urlopen(game_query_url)
        data = json.loads(response.read())
        game_json = data["gameData"]
        
        team_names = ["{0} ({1})".format(game_json["teams"][ha]["name"], game_json["teams"][ha]["abbreviation"])
                      for ha in ("away", "home")]
        self.title = "{0} - {1}".format(team_names[0], team_names[1])
        self.title_short = "{0} - {1}".format(game_json["teams"]["away"]["abbreviation"],
                                              game_json["teams"]["home"]["abbreviation"])
        self.highlights = []
        self.fanart = None
        self.thumb = None
        self.icon = None
        self.description = None
        self.description_short = None

    def get_content(self):
        images_query_url = "https://statsapi.mlb.com/api/v1/game/{0}/content".format(self.gameId)
        response = urllib.urlopen(images_query_url)
        data = json.loads(response.read())

        try:
            recap_json = data["editorial"]["recap"]["mlb"]
            self.fanart = get_image_url(recap_json, FANART_SIZE)
            self.thumb = get_image_url(recap_json, THUMB_SIZE)
            self.icon = get_image_url(recap_json, ICON_SIZE)
            self.description = recap_json["blurb"]
            self.description_short = recap_json["headline"]
        except KeyError:
            pass

    def get_highlights(self):
        highlights_query_url = "https://statsapi.mlb.com/api/v1/game/{0}/content".format(self.gameId)
        response = urllib.urlopen(highlights_query_url)
        data = json.loads(response.read())
        
        try:            
            highlights_json = data["highlights"]["highlights"]["items"]
        except KeyError:
            highlights_json = None

        if highlights_json is not None:
            self.highlights = [Highlight(h) for h in highlights_json]
            self.highlights = [h for h in self.highlights if h.url is not None]
        else:
            self.highlights = []

        # move recap, condensed game to front
        try:
            hl_recap = next(hl for hl in self.highlights if hl.contentType == "R")
            self.highlights.insert(0, self.highlights.pop(self.highlights.index(hl_recap)))
            hl_cond = next(hl for hl in self.highlights if hl.contentType == "C")
            self.highlights.insert(0, self.highlights.pop(self.highlights.index(hl_cond)))
        except StopIteration:
            pass

    def __unicode__(self):
        x = u"--- {0}".format(self.title)
        for (i, h) in enumerate(self.highlights):
            x += u"\n--- Video No. {0}\n{1}".format(i, h)
        return x

    def __str__(self):
        return unicode(self).encode('utf-8')

    
class GameDay:
    # members:
    # - date
    # - games
    def __init__(self, date):
        self.date = date

        query_url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={0}&endDate={0}&hydrate=team".format(self.date)
        response = urllib.urlopen(query_url)
        data = json.loads(response.read())

        try:
            games_json = data["dates"][0]["games"]
        except KeyError:
            games_json = None

        if games_json is not None:
            self.games = [Game(game["gamePk"]) for game in games_json]
        else:
            self.games = None

    def __unicode__(self):
        x = u"--- GameDay: {0}".format(self.date)
        for (i, g) in enumerate(self.games):
            x += u"\n--- Game No. {0}\n{1}".format(i, g)
        return x

    def __str__(self):
        return unicode(self).encode('utf-8')
