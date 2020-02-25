from string import Template
import datetime


class Endpoints:
    _games = Template("http://data.nba.com/data/5s/json/cms/noseason/scoreboard/${date}/games.json")
    _play_by_play = Template("http://data.nba.com/data/5s/json/cms/noseason/game/${date}/${game_id}/pbp_all.json")
    _box_score = Template("http://data.nba.com/data/5s/json/cms/noseason/game/${date}/${game_id}/boxscore.json")
    _schedule = Template("http://data.nba.com/data/10s/prod/v1/${season}/schedule.json")

    @staticmethod
    def games(date) -> str:
        if isinstance(date, (datetime.date, datetime.datetime)):
            date = date.strftime('%Y%m%d')
        return Endpoints._games.substitute(date=date)

    @staticmethod
    def play_by_play(date, game_id) -> str:
        if isinstance(date, (datetime.date, datetime.datetime)):
            date = date.strftime('%Y%m%d')
        return Endpoints._play_by_play.substitute(date=date, game_id=game_id)

    @staticmethod
    def box_score(date, game_id) -> str:
        if isinstance(date, (datetime.date, datetime.datetime)):
            date = date.strftime('%Y%m%d')
        return Endpoints._box_score.substitute(date=date, game_id=game_id)

    @staticmethod
    def schedule(season) -> str:
        return Endpoints._schedule.substitute(season=season)
