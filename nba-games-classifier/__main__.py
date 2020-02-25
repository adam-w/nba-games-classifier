import argparse
import datetime
import pandas as pd
import dateutil
import requests

from endpoints import Endpoints
from classifier import calculate_rating, calculate_stats


def rate_games(args) -> None:
    dates = set()
    if args.range:
        for r in args.range:
            start_date = min(r[0], r[1])
            end_date = max(r[0], r[1])
            while start_date <= end_date:
                dates.add(start_date)
                start_date += datetime.timedelta(days=1)
    dates.update(set(args.date))
    if not dates:
        dates.add(datetime.date.today() - datetime.timedelta(days=1))

    games = []
    for d in dates:
        r = requests.get(Endpoints.games(d))
        r.raise_for_status()
        games_data = r.json()
        for game in games_data['sports_content']['games']['game']:
            try:
                stats = calculate_stats(d, game['id'])
                rating, partial_ratings = calculate_rating(stats)
                stats.update(partial_ratings, rating=rating, id=game['id'], name=game['game_url'])
                games.append(stats)
            except Exception as e:
                print(e)
    if not games:
        return

    df = pd.DataFrame(games)
    df.sort_values('rating', ascending=False, inplace=True)

    if args.clipboard:
        df.to_clipboard()
    if args.output_csv:
        df.to_csv(args.output_csv)

    for index, row in df.iterrows():
        print(row['name'], row['rating'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('date', type=lambda s: dateutil.parser.parse(s).date(), nargs='*')
    parser.add_argument('-r', '--range', type=lambda s: dateutil.parser.parse(s).date(), nargs=2, help='date range',
                        action='append')
    parser.add_argument('-c', '--clipboard', action='store_true', help='copy details to clipboard')
    parser.add_argument('-o', '--output-csv', help='save details to CSV')
    args = parser.parse_args()

    rate_games(args)
