import json
import pathlib
import json
import re
import asyncio
import asyncio
import logging
import pandas as pd
import datetime
from typing import Any, Callable, Iterator
from functools import lru_cache
import argparse


logger = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).parent.absolute()

DATA_DIR = BASE_DIR.joinpath('data')

FILES = list(DATA_DIR.glob('*.json'))

CORRECTED_PATH = BASE_DIR.joinpath('corrected')

COUNTRIES_PATH = BASE_DIR.parent.joinpath('geo', 'countries.json')

TOURNAMENT_NAMES_PATH = BASE_DIR.joinpath('tournament_names.json')

COUNTRIES_BY_CONTINENT_PATH = BASE_DIR.parent.joinpath(
    'geo',
    'countries_by_continent_and_fifa.json'
)

LOCK = asyncio.Lock()

SEEN_TOURNAMENT_NAMES: set[str] = set()

with COUNTRIES_PATH.open() as f:
    countries: list[dict[str, Any]] = json.load(f)

with COUNTRIES_BY_CONTINENT_PATH.open() as f:
    countries_by_continent: list[dict[str, str]] = json.load(f)


@lru_cache(maxsize=None)
def get_continent_by_country(value: str | None) -> list[dict[str, Any]]:
    """This function is similar to `get_country` but it searches in the 
    `countries_by_continent` dataset which contains additional information about the 
    continent and subcontinent of each country. It first tries to find a match using 
    the alpha-3 code, and if that fails, it tries to find a match using the FIFA code."""
    if value is None:
        return []

    def verifier(incoming_value: dict[str, Any]) -> bool:
        return any([
            incoming_value['country'].lower() == value.lower(),
            incoming_value['code_alpha_2'].lower() == value.lower(),
            incoming_value['code_alpha_3'].lower() == value.lower(),
            incoming_value['fifa'].lower() == value.lower(),
            incoming_value['alternative_name'] and any(
                alt_name.lower() == value.lower()
                for alt_name in incoming_value['alternative_name']
            )
        ])

    return list(filter(verifier, countries_by_continent))


async def write_to_file(data: list, file_path: pathlib.Path):
    new_file_path = CORRECTED_PATH / (file_path.stem + '_corrected.json')
    with new_file_path.open('w') as f:
        json.dump(data, f, indent=4)


async def write_to_csv(data: list[dict[str, Any]], file_path: pathlib.Path):
    """A helper function that flattens the JSON data structure into a list of dictionnaries
    that can used to create a pandas DataFrame."""
    flattened: list[dict[str, Any]] = []

    fields_to_rename = {
        'code_alpha_2': 'tour_code_alpha_2',
        'code_alpha_3': 'tour_code_alpha_3',
        'country_code_m49': 'tour_country_code_m49',
        'region_code': 'tour_region_code',
        'region': 'tour_region',
        'subregion': 'tour_subregion',
        'fifa': 'tour_fifa',
    }

    for tournament in data:
        matches = tournament.pop('matches', [])

        _tournament = {}
        for key, value in tournament.items():
            if key in fields_to_rename:
                _tournament[fields_to_rename[key]] = value
                continue
            _tournament[key] = value

        for match in matches:
            # Convert the splitted_score field from a list
            # of lists to a string representation
            _splitted_score: list[
                list[int | None]
            ] = match.pop('splitted_score', [])
            splitted_score = '|'.join(
                ','.join(map(str, inner))
                for inner in _splitted_score
            )
            match['splitted_score'] = splitted_score

            # Do the same for the alternative_name field
            _alternative_name: list[str] = match.pop('alternative_name', [])
            alternative_name = '|'.join(_alternative_name)
            match['alternative_name'] = alternative_name

            flattened.append(_tournament | match)

    new_file_path = CORRECTED_PATH / (file_path.stem + '_corrected.csv')
    with new_file_path.open('w') as f:
        df = pd.DataFrame(flattened)
        df.to_csv(f, index=False)


def clean_location(data: dict):
    """Fixes the location field by removing the date and replacing 
    multiple spaces with a single space."""
    clean_location = re.sub(r'\s+', ' ', data['location'])
    data['location'] = clean_location


def get_location(data: dict[str, str]):
    """Extracts the location from the location field by removing the date.
    Should be applied once the location field has been cleaned."""
    location = data['location']
    location = location.strip().removesuffix(',')

    city = None
    state = None

    if 'UNITED STATES' in location or 'USA' in location:
        regexes = [
            r'^(.*) \• ([A-Z]{2}), .*$',
            r'^(.*) \• (?:UNITED\s?STATES|USA), ([A-Z]{2})$',
            r'^(.*) \• (?:UNITED\s?STATES|USA)$'
        ]

        for regex in regexes:
            match = re.match(regex, location)
            if match:
                city = match.group(1).title()
                state = match.group(2) if match.lastindex >= 2 else None
                break

        # Handle special cases for city
        # names in the United States
        match city:
            case 'New York':
                state = 'NY'
            case 'Indian Wells':
                state = 'CA'
            case 'Miami':
                state = 'FL'
            case 'Flushing Meadows':
                state = 'NY'
            case 'Newport':
                state = 'RI'
            case 'Fort Worth':
                state = 'TX'

        # If both the regexes fail, just split the string
        # and return only the state/city part
        if state is None:
            values = location.split(
                '•') if '•' in location else location.split(',')
            result = values[-1]
            match result.lower():
                case 'indian wells':
                    state = 'CA'
                    city = 'Indian Wells'

        country = 'United States of America'
    else:
        separator = '•' if '•' in location else ','
        tokens = location.split(separator)

        if len(tokens) == 1:
            country = tokens[0].capitalize()
        else:
            city, country = tokens
            city = city.title()
            country = country.title()

    # Normalize USA to United States of America
    if country.lower() == 'usa':
        country = 'United States of America'

    # Handle special cases for city names
    match city:
        case 'Flushing Meadows':
            city = 'New York'

    data['city'] = city.strip() if city is not None else None
    data['country'] = country.strip() if country is not None else None
    data['state'] = state

    if state is not None:
        data['state'] = state.strip()

    data.pop('location')


def start_end_date(data: dict):
    """Extract start and end date from location field and add them as 
    separate fields in the data dictionary."""
    date_regex = r'\d+ - \d+ .*'

    location = data['location']

    if location == '' or location is None:
        data['start_date'] = None
        data['end_date'] = None
        data['year'] = None
        data['month'] = None
        return

    result = re.search(date_regex, location)
    if result is not None:
        # Resolve this format: 22 - 28 Jun 2025
        date_tokens = result.group().split('-')
        tokens = list(map(lambda x: x.strip(), date_tokens))

        d, m, y = tokens[1].split(' ')
        month = datetime.datetime.strptime(m, '%b').month

        start_date = datetime.datetime(int(y), month, int(tokens[0]))
        end_date = datetime.datetime(int(y), month, int(d))
        # Remove the date from the location field
        data['location'] = re.sub(date_regex, '', location)
    else:
        # Result this format: NEW YORK • USA, 24 Aug - 7 Sep 2025
        result = re.search(r'\d+ \w+ - \d+ .*', location)

        if result is None:
            data['start_date'] = None
            data['end_date'] = None
            data['year'] = None
            data['month'] = None
            return

        date_tokens = result.group().split('-')
        tokens = list(map(lambda x: x.strip(), date_tokens))

        year = re.search(r'\d{4}$', tokens[1])
        if year is None:
            data['start_date'] = None
            data['end_date'] = None
            data['year'] = None
            data['month'] = None
            return
        else:
            tokens[0] = tokens[0] + ' ' + year.group()

        start_date = datetime.datetime.strptime(tokens[0], '%d %b %Y')
        end_date = datetime.datetime.strptime(tokens[1], '%d %b %Y')

        # Remove the date from the location field
        data['location'] = re.sub(r'\d+ \w+ - \d+ .*', '', location)

    data['start_date'] = start_date.date().isoformat()
    data['end_date'] = end_date.date().isoformat()
    data['year'] = start_date.year
    data['month'] = start_date.month


def correct_score(value: str):
    """Corrects the score by replacing multiple spaces with a single space."""
    return re.sub(r'\s+', ' ', value)


def _is_tibreak(score: str) -> bool:
    """Checks if the score is a tiebreak score."""
    result1 = re.match(r'^6(?:\d+) - 7', score)
    if result1:
        return True

    result2 = re.match(r'^7 - 6(?:\d+)', score)
    if result2:
        return True

    return False


def _create_tiebreak_tuple(values: list[int], lhv: str, rhv: str = '') -> list[int]:
    """Creates a tuple of the form (6, 7, tiebreak_score) or 
    (7, 6, tiebreak_score) depending on the score."""
    if f'{lhv}'.startswith('6'):
        result = re.match(r'^6(\d+)', f'{lhv}')
        if result:
            values[0] = 6
            values[1] = 7
            values.append(int(result.group(1)))

    if f'{lhv}'.startswith('7'):
        result = re.match(r'^6(\d+)', f'{rhv}')
        if result:
            values[0] = 7
            values[1] = 6
            values.append(int(result.group(1)))


def score_analysis(data: dict[str, str], value: str):
    """Analyzes the score and adds additional fields to the data dictionary:

    * `retired`: A boolean indicating if the player retired in the match.
    * `walkover`: A boolean indicating if the match was a walkover.
    * `bye`: A boolean indicating if the match was a bye.
    * `first_set_tiebreak`: A boolean indicating if the first set was a tiebreak.
    * `second_set_tiebreak`: A boolean indicating if the second set was a tiebreak.
    * `third_set_tiebreak`: A boolean indicating if the third set was a tiebreak.
    * `has_tiebreak`: A boolean indicating if any of the sets was a tiebreak.
    * `splitted_score`: A list of tuples representing the scores for each set.
    * `number_of_sets`: An integer representing the number of sets played in the match.
    * `first_set_won`: A boolean indicating if the first set was won by the winner of the match.
    * `total_games`: An integer representing the total number of games played in the match.
    * `winner_games`: An integer representing the total number of games won by the winner of the match.
    * `loser_games`: An integer representing the total number of games won by the loser of the match.
    * `score`: A string representing the corrected score of the match.
    """
    # Check if the player retired in the match
    data['retired'] = False
    data['walkover'] = False
    data['bye'] = False

    if value.endswith('Ret'):
        data['retired'] = True

    if value == 'Walkover':
        data['walkover'] = True

    if value == 'Bye':
        data['bye'] = True

    _str_scores = value.split(',')
    str_scores = list(filter(lambda x: x.strip() != '', _str_scores))

    # Check the tiebreaks for each set and add them
    #  as separate fields in the data dictionary
    data['first_set_tiebreak'] = False
    data['second_set_tiebreak'] = False
    data['third_set_tiebreak'] = False

    if len(str_scores) > 1:
        data['first_set_tiebreak'] = _is_tibreak(str_scores[0])
        data['second_set_tiebreak'] = _is_tibreak(str_scores[1])

    if len(str_scores) > 2:
        data['third_set_tiebreak'] = _is_tibreak(str_scores[2])

    data['has_tiebreak'] = any([
        data['first_set_tiebreak'],
        data['second_set_tiebreak'],
        data['third_set_tiebreak']
    ])

    # Get the numerical scores as a list of tuples
    _scores: list[tuple[int, int, int | None]] = []
    for i, score in enumerate(str_scores):
        # [('5', '7'), ('6', '1'), ('1', '6')]
        _values: Iterator[tuple[str, str]] = map(
            lambda x: x.strip(), score.split('-'))

        # [6, 1]
        values: list[int] = []
        for v in _values:
            if v.isdigit():
                values.append(int(v))
            else:
                values.append(v)

        # Rebuild the tuple to be (6, 7, x) if the first
        # set is a tiebreak and the score starts with 6.
        # Other sets that are not tiebreks would be
        # (6, 1, null) or (1, 6, null)
        if not data['walkover'] and not data['bye']:
            # Safeguard for when a player retires after the first set. Therefore
            # we only have a score the first set
            if data['retired']:
                if len(values) == 1:
                    _create_tiebreak_tuple(values, values[0])
            else:
                if values:
                    lhv, rhv = values
                    if data['first_set_tiebreak'] and i == 0:
                        _create_tiebreak_tuple(values, lhv, rhv)

                    if data['second_set_tiebreak'] and i == 1:
                        _create_tiebreak_tuple(values, lhv, rhv)

                    if data['third_set_tiebreak'] and i == 2:
                        _create_tiebreak_tuple(values, lhv, rhv)

            # Normalize the score to be a tuple of the form (6, 1, null)
            # or (1, 6, null) for non-tiebreak sets in order to have a
            # consistent format for all sets.
            if len(values) == 2:
                values.append(None)

            _scores.append(tuple(values))

    data['splitted_score'] = _scores
    data['number_of_sets'] = len(_scores)

    data['first_set_won'] = False
    # Check if the first set was won by
    # the winner of the match
    if len(str_scores) > 1:
        if str_scores[0].startswith('6 -') or str_scores[0].startswith('7 -'):
            data['first_set_won'] = True

    # Correct the count for the scores
    # that contain walkover or bye
    for item in _scores:
        if len(item) == 1:
            if item[0] == 'Walkover' or item[0] == 'Bye':
                data['number_of_sets'] = 0

            if item[0] == 'Ret':
                data['number_of_sets'] = data['number_of_sets'] - 1

    # Also correct the text score
    fixed_score = []
    for item in _scores:
        if len(item) == 1:
            continue

        if item[2] is None:
            value = '-'.join(
                str(x) for x in filter(lambda x: x is not None, item)
            )
            fixed_score.append(value)
            continue
        else:
            lhv, rhv, tiebreak_score = item
            value = f'{lhv}-{rhv} ({tiebreak_score})'
            fixed_score.append(value)

    if fixed_score:
        data['score'] = ', '.join(fixed_score)

    # Calculate the total number of games and those
    # won by the winner and the loser
    data['total_games'] = 0
    data['winner_games'] = 0
    data['loser_games'] = 0

    for item in _scores:
        if len(item) == 1:
            continue

        lhv, rhv, _ = item
        if isinstance(lhv, int) and isinstance(rhv, int):
            data['total_games'] += lhv + rhv
            data['winner_games'] += lhv
            data['loser_games'] += rhv


def _set_country_details(data: dict[str, Any]):
    """Sets the country details in the data dictionary by looking up 
    the country code in the countries_by_continent.json file. Adds the
    following fields to the data dictionary:

    * `alternative_name`: A list of alternative names for the country.
    * `code_alpha_2`: The ISO 3166-1 alpha-2 code for the country.
    * `code_alpha_3`: The ISO 3166-1 alpha-3 code for the country.
    * `country_code_m49`: The UN M.49 code for the country.
    * `region_code`: The UN M.49 region code for the country.
    * `region`: The UN M.49 region name for the country.
    * `subregion`: The UN M.49 subregion name for the country.
    * `fifa`: The FIFA code for the country.
    """
    country_code: str = data['country']

    result = get_continent_by_country(country_code)
    if not result:
        result = {
            "alternative_name": [],
            "code_alpha_2": None,
            "code_alpha_3": None,
            "country_code_m49": None,
            "region_code": None,
            "region": None,
            "subregion": None,
            "fifa": country_code
        }
    else:
        result = result[0].copy()
        result.pop('country')
    data.update(result)


async def correct_data(tournament: dict[str, str | list[str]]) -> list:
    """Main entry function to correct the data by applying all the fixes to the data dictionary.
    """
    fixes: list[Callable[[dict[str, str | list[str]]], None]] = [
        clean_location,
        start_end_date,
        get_location
    ]

    for fix in fixes:
        fix(tournament)

    for item in tournament['matches']:
        # Scores
        item['score'] = correct_score(item['score'])
        score_analysis(item, item['score'])

        # Correct the seed field by extracting the number
        # from the string and converting it to an integer
        if item['seed'] is not None:
            result = re.search(r'\d+', item['seed'])
            if result is not None:
                item['seed'] = int(result.group())

        # Convert the rank field to an integer
        if item['rank'] is not None:
            try:
                item['rank'] = int(item['rank'])
            except ValueError:
                item['rank'] = None

        # Fix the round field by replacing
        # multiple spaces with a single space
        if item['round'] is not None:
            result = re.sub(r'\s+', ' ', item['round']).strip()
            match result:
                case 'Quarterfinals Quarter':
                    item['round'] = 'QF'
                case 'Semifinals Semi':
                    item['round'] = 'SF'
                case 'Final F':
                    item['round'] = 'F'
                case 'Round of 16 R16':
                    item['round'] = 'R16'
                case 'Round of 32 R32':
                    item['round'] = 'R32'
                case 'Round of 64 R64':
                    item['round'] = 'R64'
                case 'Round of 128 R128':
                    item['round'] = 'R128'
                case 'Qualifying R3 Qual. R3':
                    item['round'] = 'QR3'
                case 'Qualifying R2 Qual. R2':
                    item['round'] = 'QR2'
                case 'Qualifying R1 Qual. R1':
                    item['round'] = 'QR1'
                case 'Group Stage Group':
                    item['round'] = 'RR'
                case _:
                    item['round'] = result

        # Add a numeric win/loss indicator for the
        # winner and loser of the match
        if item['win_loss'] == 'W':
            item['win_loss_numeric'] = 1
        elif item['win_loss'] == 'L':
            item['win_loss_numeric'] = 0

        if item['bye']:
            item['win_loss_numeric'] = 0

        if item['walkover']:
            item['win_loss_numeric'] = 0

        # Add country details for the player
        _set_country_details(item)

    # Add details for the country related to the tournament
    _set_country_details(tournament)

    # Fix the "meta" field
    meta = tournament.pop('meta')
    for item in meta:
        if 'Rank:' in item:
            tournament['rank'] = int(item.removeprefix('Rank:').strip())

        # Add simple boolean field to indicate if the
        # player entered the tournament as a wild card
        if 'Entry Type:' in item:
            tournament['entry_type'] = item.removeprefix('Entry Type:').strip()
            tournament['wild_card_entry'] = False
            if tournament['entry_type'] == 'W':
                tournament['wild_card_entry'] = True

        if 'WTA Points Gain: WTA Points:' in item:
            points = item.removeprefix('WTA Points Gain: WTA Points:').strip()
            tournament['points_gain'] = int(points.removeprefix('+'))

        if 'Prize Money Won: Prize Money:' in item:
            prize_money = item.removeprefix(
                'Prize Money Won: Prize Money:'
            ).strip()
            tournament['prize_money'] = int(prize_money.removeprefix(
                '+').removeprefix('$').replace(',', ''))
        if 'Draw:' in item:
            draw = item.removeprefix('Draw:').strip()
            tournament['draw'] = draw

    # The custom name is the name listed exactly as it appears in the WTA website.
    tournament['custom_title'] = tournament['title'].lower().title()
    # Add and alternative name field for the tournament. This is done because some events have
    # rebranded anems over the years. For example, the "Australian Open" was previously
    # known as the "Australian Championships" and for Nuxt, we need to have a way to map
    # the old name to the new name.
    tournament['alt_titles'] = '|'.join([])

    # This is the normalized name of the tournament that will be used for frontend
    # applications. It allows for example for "Wimbledon" also referenced as "The Championships"
    # to be mapped to the same name.

    match tournament['title'].lower():
        case 'the championships':
            tournament['title'] = 'Wimbledon'
        case 'the championships, wimbledon':
            tournament['title'] = 'Wimbledon'
        case 'championnats internationaux de france':
            tournament['title'] = 'Roland Garros'
        case 'roland garros- paris, france':
            tournament['title'] = 'Roland Garros'
        case 'olympic tennis event':
            tournament['title'] = 'Olympic Games'
        case _:
            # Just use the custom name as the normalized name
            # if no special case is found
            tournament['title'] = tournament['custom_title']

    # Calculate the total number of games played in the tournament,
    # the average number of games per match, and the total number of
    # matches played in the tournament.
    valid_matches = list(
        filter(
            lambda x: x['bye'] is False and x['walkover'] is False,
            tournament['matches']
        )
    )
    games = sum(match['total_games'] for match in valid_matches)
    matches = len(valid_matches)
    avg_games = games / matches if matches > 0 else 0

    tournament['tour_total_games'] = games
    tournament['tour_total_matches'] = matches
    tournament['tour_avg_games'] = avg_games

    tournament['tour_sets_played'] = sum(
        match['number_of_sets']
        for match in valid_matches
    )

    tournament['tour_avg_sets_played'] = tournament['tour_sets_played'] / \
        matches if matches > 0 else 0

    return tournament


async def write_tournament_name(data: dict):
    """Writes the tournament name to a text file."""
    async with LOCK:
        with TOURNAMENT_NAMES_PATH.open('r+') as f:
            actual_data = json.load(f)
            actual_data.append(data)
            f.seek(0)
            json.dump(actual_data, f, indent=4)


async def collect_tournament_names(task_group: asyncio.TaskGroup, data: list[dict[str, str | list[str]]]):
    """Collects the tournament names from the data dictionary and adds them to the task group."""
    await LOCK.acquire()
    names = {tournament['title'] for tournament in data}
    SEEN_TOURNAMENT_NAMES.update(names)

    for name in SEEN_TOURNAMENT_NAMES:
        data: dict = {
            'title': name,
            'alt_title': None,
            'related_titles': None,
            'geo': {
                'lat': None,
                'lng': None,
            }
        }
        task_group.create_task(write_tournament_name(data))

    LOCK.release()


async def main():
    for _, item in enumerate(FILES):
        logger.info(f'* Correcting data in file: {item.name}')

        with item.open() as f:
            data: list[dict[str, str | list[str]]] = json.load(f)
            for i, tournament in enumerate(data):
                # Before correcting, ensure that we have a good
                # numbering for the ID field
                tournament['id'] = i + 1
                await correct_data(tournament)

            task = asyncio.create_task(write_to_file(data, item))
            await task

            task = asyncio.create_task(write_to_csv(data, item))
            await task

            async with asyncio.TaskGroup() as tg:
                tg.create_task(collect_tournament_names(tg, data))

        logger.info(f'+ Finished correcting data in file: {item.name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Correct the data in the JSON files .'
    )

    parser.add_argument(
        '--file',
        type=str,
        help='The path to the JSON file to correct. If not provided, all JSON files in the data directory will be corrected.'
    )
    args = parser.parse_args()

    asyncio.run(main())
