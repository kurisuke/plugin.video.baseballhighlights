# -*- coding: utf-8 -*-
# Module: default
# Author: Peter Helbing (original: Roman V. M.)
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin

import datetime
import dateutil.parser

import baseballhighlights

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_gamedays():
    current_date = datetime.date.today()
    gamedays = []
    start_end_dates = baseballhighlights.get_season_dates(current_date.year)
    if start_end_dates is not None:
        opening_day = start_end_dates[0]
        while current_date >= opening_day:
            gamedays.append(current_date)
            current_date -= datetime.timedelta(1)
    return gamedays


def list_top():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Baseball Highlights')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    list_item = xbmcgui.ListItem(label="Games by Date")
    list_item.setInfo('video', {'title': "Games by Date", 'mediatype': 'video'})
    url = get_url(mode='bydate')
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    list_item = xbmcgui.ListItem(label="Games by Team")
    list_item.setInfo('video', {'title': "Games by Team", 'mediatype': 'video'})
    url = get_url(mode='byteam')
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_bydate():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Games by date')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    gamedays = get_gamedays()
    # Iterate through categories
    for gameday in gamedays:
        gameday_label = "{0}".format(gameday)
        gameday_sort = "{:02d}.{:02d}.{:04d}".format(gameday.day, gameday.month, gameday.year)
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=gameday_label)
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': gameday_label,
                                    'date': gameday_sort,
                                    'mediatype': 'video'})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(mode='gameday', date=gameday_label)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def get_gameday(date_str):
    date = dateutil.parser.parse(date_str).date()
    return baseballhighlights.GameDay(date)


def list_gameday(date):
    """
    Create the list of games for the Kodi Interface.

    :param date: Date for games in format YYYY-MM-DD
    :type date: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, date)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    gameday = get_gameday(date)
    # Iterate through categories
    for game in gameday.games:
        game.get_content()
        # Only add if there are media available
        if game.description is not None:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=game.title)
            # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
            # Here we use the same image for all items for simplicity's sake.
            # In a real-life plugin you need to set each image accordingly.
            list_item.setArt({'thumb': game.thumb, 'icon': game.icon, 'fanart': game.fanart})
            # Set additional info for the list item.
            # Here we use a category name for both properties for for simplicity's sake.
            # setInfo allows to set various information for an item.
            # For available properties see the following link:
            # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
            # 'mediatype' is needed for a skin to display info for this ListItem correctly.
            list_item.setInfo('video', {'title': game.title,
                                        'plot': game.description,
                                        'plotoutline': game.description_short,
                                        'mediatype': 'video'})
            # Create a URL for a plugin recursive call.
            # Example: plugin://plugin.video.example/?action=listing&category=Animals
            url = get_url(mode='game', gameId=game.gameId)
            # is_folder = True means that this item opens a sub-list of lower level items.
            is_folder = True
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def get_teams():
    return baseballhighlights.get_teams()


def list_byteam():
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, "Games by Team")
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    teams = get_teams()
    for team in teams:
        label = "{0} ({1})".format(team.name, team.abbreviation)
        logo = "http://www.mlbstatic.com/mlb.com/images/share/{0}.jpg".format(team.team_id)
        list_item = xbmcgui.ListItem(label=label)
        list_item.setArt({'thumb': logo, 'icon': logo})
        list_item.setInfo('video', {'title': label,
                                    'mediatype': 'video'})
        url = get_url(mode='gamesbyteam', teamId=str(team.team_id))
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def get_gamesbyteam(team_id):
    date_end = datetime.date.today()
    date_start = datetime.date.today() - datetime.timedelta(30)
    return baseballhighlights.GamesByTeam(date_start, date_end, team_id)


def list_gamesbyteam(team_id):
    """
    Create the list of games for the Kodi Interface.

    :param team_id: Team ID from MLB API
    :type team_id: int
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, "Games by Team")
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    gamesbyteam = get_gamesbyteam(team_id)
    # Iterate through categories
    for game in gamesbyteam.games:
        game.get_content()
        # Only add if there are media available
        if game.description is not None:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=game.title_time)
            game_date_str = "{:02d}.{:02d}.{:04d}".format(game.datetime.day, game.datetime.month, game.datetime.year)
            # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
            # Here we use the same image for all items for simplicity's sake.
            # In a real-life plugin you need to set each image accordingly.
            list_item.setArt({'thumb': game.thumb, 'icon': game.icon, 'fanart': game.fanart})
            # Set additional info for the list item.
            # Here we use a category name for both properties for for simplicity's sake.
            # setInfo allows to set various information for an item.
            # For available properties see the following link:
            # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
            # 'mediatype' is needed for a skin to display info for this ListItem correctly.
            list_item.setInfo('video', {'title': game.title_time,
                                        'plot': game.description,
                                        'date': game_date_str,
                                        'plotoutline': game.description_short,
                                        'mediatype': 'video'})
            # Create a URL for a plugin recursive call.
            # Example: plugin://plugin.video.example/?action=listing&category=Animals
            url = get_url(mode='game', gameId=game.gameId)
            # is_folder = True means that this item opens a sub-list of lower level items.
            is_folder = True
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
    

def get_highlights(game_id):
    g = baseballhighlights.Game(game_id)
    g.get_content()
    g.get_highlights()
    return g

    
def list_highlights(game_id):
    """
    Create the list of playable videos in the Kodi interface.

    :param game_id: Game ID (from MLB Stats API)
    :type game_id: str
    """
    # Get the list of videos in the category.
    game = get_highlights(game_id)
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, game.title_short)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    # Iterate through videos.
    for (i, highlight) in enumerate(game.highlights):
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=highlight.title)
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': highlight.title,
                                    'plot': highlight.description,
                                    'plotoutline': highlight.description_short,
                                    'duration': highlight.duration,
                                    'mediatype': 'video', 'episode': i})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': highlight.thumb, 'icon': highlight.icon, 'fanart': highlight.fanart})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        url = get_url(mode='highlight', video=highlight.url)
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_EPISODE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['mode'] == 'bydate':
            # Display the list of games for a gameday.
            list_bydate()
        elif params['mode'] == 'byteam':
            # Display the list of games for a gameday.
            list_byteam()
        elif params['mode'] == 'gameday':
            # Display the list of games for a gameday.
            list_gameday(params['date'])
        elif params['mode'] == 'gamesbyteam':
            # Display the list of games for a gameday.
            list_gamesbyteam(params['teamId'])
        elif params['mode'] == 'game':
            # Display the list of highlights for a game.
            list_highlights(params['gameId'])
        elif params['mode'] == 'highlight':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display a list of the last 7 days or so
        list_top()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
