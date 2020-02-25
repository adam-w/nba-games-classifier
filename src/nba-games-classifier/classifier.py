from typing import Dict, Union, Tuple
import requests
import numpy as np

from endpoints import Endpoints


def _calc_box_score_stats(bs) -> Dict[str, Union[float, int]]:
    stats = dict()

    vs = bs['sports_content']['game']['visitor']['stats']
    hs = bs['sports_content']['game']['home']['stats']

    stats['field_goals_made'] = int(vs['field_goals_made']) + int(hs['field_goals_made'])
    stats['field_goals_attempted'] = int(vs['field_goals_attempted']) + int(hs['field_goals_attempted'])
    stats['field_goals_percentage'] = stats['field_goals_made'] / stats['field_goals_attempted']

    stats['free_throws_made'] = int(vs['free_throws_made']) + int(hs['free_throws_made'])
    stats['free_throws_attempted'] = int(vs['free_throws_attempted']) + int(hs['free_throws_attempted'])
    stats['free_throws_percentage'] = stats['free_throws_made'] / stats['free_throws_attempted']

    stats['three_pointers_made'] = int(vs['three_pointers_made']) + int(hs['three_pointers_made'])
    stats['three_pointers_attempted'] = int(vs['three_pointers_attempted']) + int(hs['three_pointers_attempted'])
    stats['three_pointers_percentage'] = stats['three_pointers_made'] / stats['three_pointers_attempted']

    periods = int(bs['sports_content']['game']['period_time']['period_value'])
    stats['game_time_multiplier'] = (min(4, periods) * 12 + max(0, periods - 4) * 5) / (4 * 12)

    return stats


def _calc_play_by_play_stats(pbp) -> Dict[str, Union[float, int]]:
    stats = dict()

    changes_of_lead = []
    prev_hs = 0
    prev_vs = 0
    periods = 0
    min_diff = 0
    max_diff = 0
    end_diff = 0
    diff_sum = 0
    diff_changes_count = 0

    for play in pbp['sports_content']['game']['play']:
        clock = play['clock'].split(':')
        clock_seconds = (int(clock[0]) * 60 + int(clock[1])) if len(clock) == 2 else 0
        hs = int(play['home_score'])
        vs = int(play['visitor_score'])
        period = int(play['period'])
        periods = max(period, periods)
        if hs != prev_hs or vs != prev_vs:
            # Score has changed since the last event.
            prev_diff = prev_hs - prev_vs
            diff = hs - vs
            max_diff = max(max_diff, diff)
            min_diff = min(min_diff, diff)
            end_diff = diff
            if prev_diff > 0 >= diff or prev_diff < 0 <= diff:
                # Leading team has changed (does not include changes from a tie).
                changes_of_lead.append((period, clock_seconds))
            diff_sum += abs(diff)
            diff_changes_count += 1
        prev_hs = hs
        prev_vs = vs

    stats['lc_total'] = len(changes_of_lead)
    stats['lc_per_period'] = [(sum(1 if e[0] == p else 0 for e in changes_of_lead)) for p in range(1, periods + 1)]
    stats['lc_in_last_minutes'] = sum(1 if (e[0] >= 4 and e[1] <= 120) else 0 for e in changes_of_lead)
    stats['lc_when_shot_clock_off'] = sum(1 if (e[0] >= 4 and e[1] < 24) else 0 for e in changes_of_lead)
    stats['pts_amplitude'] = max(abs(min_diff), max_diff)
    stats['pts_peak_to_peak_amplitude'] = max_diff - min_diff
    stats['pts_end_difference'] = abs(end_diff)
    stats['average_pts_difference'] = diff_sum / diff_changes_count

    return stats


def calculate_stats(date, game_id) -> Dict[str, Union[float, int]]:
    r = requests.get(Endpoints.box_score(date, game_id))
    r.raise_for_status()
    bs = r.json()

    r = requests.get(Endpoints.play_by_play(date, game_id))
    r.raise_for_status()
    pbp = r.json()

    stats = dict()
    stats.update(_calc_box_score_stats(bs))
    stats.update(_calc_play_by_play_stats(pbp))

    return stats


def calculate_rating(stats : Dict[str, Union[float, int]]) -> Tuple[float, Dict[str, float]]:
    ratings = dict()
    ratings['rating_field_goals'] = (np.interp(stats['field_goals_percentage'],
                                               [0.4, 0.6], [0.0, 1.0]), 1)

    ratings['rating_three_pointers'] = (np.interp(stats['three_pointers_percentage'],
                                                  [0.3, 0.5], [0.0, 1.0]), 2)

    ratings['rating_free_throws'] = (np.interp(stats['free_throws_attempted'] / stats['game_time_multiplier'],
                                               [30, 70], [1.0, 0.0]), 1)

    ratings['rating_early_game_lc'] = (np.interp(sum(stats['lc_per_period'][0:1]),
                                                 [0, 6], [0.0, 1.0]), 1)

    ratings['rating_mid_game_lc'] = (np.interp(sum(stats['lc_per_period'][1:3]),
                                               [0, 10], [0.0, 1.0]), 3)

    ratings['rating_late_game_lc'] = (np.interp(sum(stats['lc_per_period'][3:]),
                                                [0, 6], [0.0, 1.0]), 4)

    ratings['rating_last_minutes_lc'] = (np.interp(stats['lc_in_last_minutes'],
                                                   [0, 2], [0.5, 1.0]), 6 if stats['lc_in_last_minutes'] else 0)

    ratings['rating_clock_off_lc'] = (np.interp(stats['lc_when_shot_clock_off'],
                                                [0, 1], [0.0, 1.0]), 10 if stats['lc_when_shot_clock_off'] else 0)

    ratings['rating_pts_difference'] = (np.interp(stats['average_pts_difference'],
                                                  [0, 20], [1.0, 0.0]), 4)

    ratings['rating_final_score'] = (np.interp(stats['pts_end_difference'],
                                               [1, 20], [1.0, 0.0]), 4)

    values, weights = map(list, zip(*ratings.values()))
    final_rating = np.average(values, weights=weights)

    return final_rating, dict((key, value[0]) for key, value in ratings.items())
