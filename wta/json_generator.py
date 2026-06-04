import json
import pathlib
import json
import re
import asyncio
import asyncio
import datetime
from typing import Any, Iterator
from functools import lru_cache
import argparse

BASE_DIR = pathlib.Path('.').absolute()

DATA_DIR = BASE_DIR.joinpath('data')

FILES = list(DATA_DIR.glob('*.json'))

CORRECTED_PATH = BASE_DIR.joinpath('corrected')

COUNTRIES_PATH = BASE_DIR.parent.joinpath('geo', 'countries.json')

COUNTRIES_BY_CONTINENT_PATH = BASE_DIR.parent.joinpath(
    'geo',
    'countries_by_continent_and_fifa.json'
)

with COUNTRIES_PATH.open() as f:
    countries: list[dict[str, Any]] = json.load(f)

with COUNTRIES_BY_CONTINENT_PATH.open() as f:
    countries_by_continent: list[dict[str, str]] = json.load(f)


@lru_cache(maxsize=None)
def get_country(country_code: str | None) -> list[dict[str, Any]]:
    if country_code is None:
        return []

    result = list(
        filter(
            lambda x: x['code_alpha_3'].lower() == country_code.lower(),
            countries
        )
    )

    if not result:
        result = list(
            filter(
                lambda x: x['fifa'].lower() == country_code.lower(),
                countries
            )
        )

    return result


@lru_cache(maxsize=None)
def get_country_by_continent(country_code: str | None) -> list[dict[str, Any]]:
    """This function is similar to `get_country` but it searches in the 
    `countries_by_continent` dataset which contains additional information about the 
    continent and subcontinent of each country. It first tries to find a match using 
    the alpha-3 code, and if that fails, it tries to find a match using the FIFA code."""
    if country_code is None:
        return []

    result = list(
        filter(
            lambda x: x['code_alpha_3'].lower() == country_code.lower(),
            countries_by_continent
        )
    )

    if not result:
        result = list(
            filter(
                lambda x: x['fifa'].lower() == country_code.lower(),
                countries_by_continent
            )
        )
    return result


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
            r'^(.*) \• (?:UNITED\s?STATES|USA), ([A-Z]{2})$'
        ]

        for regex in regexes:
            match = re.match(regex, location)
            if match:
                city = match.group(1).title()
                state = match.group(2)

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
    result = re.search(date_regex, location)

    if location == '' or location is None:
        data['start_date'] = None
        data['end_date'] = None
        data['year'] = None
        data['month'] = None
        return

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
    """Creates a tuple of the form (6, 7, tiebreak_score) or (7, 6, tiebreak_score) depending on the score."""
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

    data['first_set_tiebreak'] = False
    data['second_set_tiebreak'] = False
    data['third_set_tiebreak'] = False

    # Check if the first set is a tiebreak
    if len(str_scores) > 1:
        data['first_set_tiebreak'] = _is_tibreak(str_scores[0])
        data['second_set_tiebreak'] = _is_tibreak(str_scores[1])

    if len(str_scores) > 2:
        data['third_set_tiebreak'] = _is_tibreak(str_scores[2])

    # Get the numerical scores as a list of tuples
    _scores: list[tuple[int, int]] = []
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

    # Correct the count for the scores that contain walkover or bye
    # data['number_of_games'] = len(_scores)
    for item in _scores:
        if len(item) == 1:
            if item[0] == 'Walkover' or item[0] == 'Bye':
                data['number_of_sets'] = 0

            if item[0] == 'Ret':
                data['number_of_sets'] = data['number_of_sets'] - 1

        # if item and (item[0] == 'Walkover' or item[0] == 'Bye'):
        #     data['number_of_games'] = 0
        # else:
        #     print(item[:2])
        #     data['number_of_games'] += sum(item[:2])


def _set_country_details(data: dict[str, Any]):
    """Sets the country details in the data dictionary by looking up 
    the country code in the countries_by_continent.json file."""
    country_code: str = data['country']

    result = get_country_by_continent(country_code)
    if not result:
        result = {
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


def correct_data(tournament: dict[str, str | list[str]]) -> list:
    """Main entry function to correct the data by applying all the fixes to the data dictionary."""
    fixes = [
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
                    item['round'] = 'Quarterfinals'
                case 'Semifinals Semi':
                    item['round'] = 'Semifinals'
                case 'Final F':
                    item['round'] = 'Finals'
                case 'Round of 16 R16':
                    item['round'] = 'Round of 16'
                case 'Round of 32 R32':
                    item['round'] = 'Round of 32'
                case 'Round of 64 R64':
                    item['round'] = 'Round of 64'
                case 'Round of 128 R128':
                    item['round'] = 'Round of 128'
                case _:
                    item['round'] = result

        # Add country details for the player
        _set_country_details(item)

    # Add details for the country related to the tournament
    _set_country_details(tournament)

    # Fix the "meta" field
    meta = tournament.pop('meta')
    for item in meta:
        if 'Rank:' in item:
            tournament['rank'] = int(item.removeprefix('Rank:').strip())

        if 'Entry Type:' in item:
            tournament['entry_type'] = item.removeprefix('Entry Type:').strip()

        if 'WTA Points Gain: WTA Points:' in item:
            points = item.removeprefix('WTA Points Gain: WTA Points:').strip()
            tournament['points_gain'] = int(points.removeprefix('+'))

        if 'Prize Money Won: Prize Money:' in item:
            prize_money = item.removeprefix(
                'Prize Money Won: Prize Money:').strip()
            tournament['prize_money'] = int(prize_money.removeprefix(
                '+').removeprefix('$').replace(',', ''))
        if 'Draw:' in item:
            draw = item.removeprefix('Draw:').strip()
            tournament['draw'] = draw
    return tournament


async def write_to_file(data: list, file_path: pathlib.Path):
    new_file_path = CORRECTED_PATH / (file_path.stem + '_corrected.json')
    with new_file_path.open('w') as f:
        json.dump(data, f, indent=4)


async def main():
    for index, item in enumerate(FILES):
        with item.open() as f:
            data = json.load(f)
            for tournament in data:
                corrected_data = correct_data(tournament)

            task = asyncio.create_task(write_to_file(data, item))
            await task


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
