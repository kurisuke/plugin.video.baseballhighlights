# -*- coding: utf-8 -*-
# Module: default
# Author: Peter Helbing
# Created on: 15.04.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import print_function

import datetime
import dateutil.parser
import dateutil.tz
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
                    break
                elif playback["name"] == "FLASH_2500K_1280X720":
                    self.url = playback["url"]
                    break
        except KeyError:
            return

        try:
            self.title = highlight_json["title"]
        except KeyError:
            self.title = ""

        try:
            self.description = highlight_json["description"]
        except KeyError:
            self.description = ""

        try:
            self.description_short = highlight_json["blurb"]
        except KeyError:
            self.description_short = ""

        try:
            self.duration = convert_duration(highlight_json["duration"])
        except KeyError:
            self.duration = 0

        self.fanart = get_image_url(highlight_json, FANART_SIZE)
        self.thumb = get_image_url(highlight_json, THUMB_SIZE)
        self.icon = get_image_url(highlight_json, ICON_SIZE)

        self.contentType = "H"
        try:
            if highlight_json["slug"].startswith("cg-"):
                self.contentType = "C"
            elif highlight_json["slug"].startswith("recap-"):
                self.contentType = "R"
        except KeyError:
            pass

    def __unicode__(self):
        return u"{0}: {1}\nurl: {2}\nthumb: {3}".format(self.contentType, self.title, self.url, self.thumb)

    def __str__(self):
        return unicode(self).encode('utf-8')


class Game:
    def __init__(self, game_desc):
        # members:
        # - gameid
        # - datetime
        # - title
        # - title_short
        # - fanart
        # - thumb
        # - icon
        # - description
        # - description_short
        # - highlights
        self.gameId = None

        self.datetime = None
        self.title = None
        self.title_short = None
        self.title_time = None

        self.fanart = None
        self.thumb = None
        self.icon = None
        self.description = None
        self.description_short = None

        self.highlights = []
        self.scores = None

        game_json = None
        if type(game_desc) == str or type(game_desc) == int:
            self.gameId = game_desc
            game_query_url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&gamePk={0}&hydrate=game(content(all)),linescore,team".format(game_desc)
            response = urllib.urlopen(game_query_url)
            data = json.loads(response.read())
            try:
                game_json = data["dates"][0]["games"][0]
            except KeyError:
                pass
        elif type(game_desc) == dict:
            try:
                self.gameId = game_desc["gamePk"]
                game_json = game_desc
            except KeyError:
                pass
        if game_json == None:
            return

        try:
            self.datetime = dateutil.parser.parse(game_json["gameDate"])
            game_time_str = self.datetime.astimezone(dateutil.tz.tzlocal()).strftime("%Y-%m-%d %H:%M")
        except KeyError:
            game_time_str = ""

        team_names = ["{0} ({1})".format(game_json["teams"][ha]["team"]["name"],
                                         game_json["teams"][ha]["team"]["abbreviation"]) for ha in ("away", "home")]
        self.title = "{0} @ {1}".format(team_names[0], team_names[1])
        self.title_short = "{0} @ {1}".format(game_json["teams"]["away"]["team"]["abbreviation"],
                                              game_json["teams"]["home"]["team"]["abbreviation"])
        self.title_time = "{0} — {1}".format(game_time_str, self.title_short)

        try:
            recap_json = game_json["content"]["editorial"]["recap"]["mlb"]
            self.fanart = get_image_url(recap_json, FANART_SIZE)
            self.thumb = get_image_url(recap_json, THUMB_SIZE)
            self.icon = get_image_url(recap_json, ICON_SIZE)
            self.description = recap_json["blurb"]
            self.description_short = recap_json["headline"]
        except KeyError:
            pass

        try:
            self.scores = (int(game_json["linescore"]["teams"]["away"]["runs"]),
                           int(game_json["linescore"]["teams"]["home"]["runs"]))
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

        query_url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={0}&endDate={0}&gameType=R&hydrate=game(content(all)),linescore,team".format(
            self.date)
        response = urllib.urlopen(query_url)
        data = json.loads(response.read())

        try:
            games_json = data["dates"][0]["games"]
        except (KeyError, IndexError), _:
            games_json = None

        if games_json is not None:
            self.games = [Game(game) for game in games_json]
        else:
            self.games = []

    def __unicode__(self):
        x = u"--- GameDay: {0}".format(self.date)
        for (i, g) in enumerate(self.games):
            x += u"\n--- Game No. {0}\n{1}".format(i, g)
        return x

    def __str__(self):
        return unicode(self).encode('utf-8')


def get_season_dates(year):
    query_url = "https://statsapi.mlb.com/api/v1/seasons?sportId=1&seasonId={0}".format(year)
    response = urllib.urlopen(query_url)
    data = json.loads(response.read())

    try:
        season_json = data["seasons"][0]
        return (dateutil.parser.parse(season_json["regularSeasonStartDate"]).date(),
                dateutil.parser.parse(season_json["regularSeasonEndDate"]).date())
    except IndexError:
        return None


class Team:
    def __init__(self, name, abbreviation, team_id):
        self.name = name
        self.abbreviation = abbreviation
        self.team_id = team_id


def get_teams():
    query_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    response = urllib.urlopen(query_url)
    data = json.loads(response.read())

    try:
        teams_json = data["teams"]
    except IndexError:
        return []

    teams = []
    for team_json in teams_json:
        teams.append(Team(team_json["name"], team_json["abbreviation"], team_json["id"]))
    return sorted(teams, key=lambda x: x.abbreviation)


class GamesByTeam:
    def __init__(self, date_start, date_end, team_id):
        query_url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={0}&endDate={1}&teamId={2}&gameType=R&hydrate=game(content(all)),linescore,team".format(
            date_start, date_end, team_id)
        response = urllib.urlopen(query_url)
        data = json.loads(response.read())

        try:
            dates_json = data["dates"]
        except KeyError:
            dates_json = []

        self.games = []
        for date_json in dates_json:
            try:
                games_json = date_json["games"]
            except KeyError:
                games_json = None

            if games_json is not None:
                for game_json in games_json:
                    self.games.append(Game(game_json))
