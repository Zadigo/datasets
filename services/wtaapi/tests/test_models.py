import pytest
from models import PlayerModel

TEST_CASES = [
    {
        "id": 10,
        "title": "Qatar TotalEnergies Open 2025",
        "logo": "https://photoresources.wtatennis.com/photo-resources/2025/04/16/74cb07bc-dc84-43f7-9acc-95e51d3748c9/WTA-Tournament_Doha-2025.png?height=128",
        "url": "https://www.wtatennis.com/tournaments/1003/doha/2025",
        "level": "WTA 1000",
        "surface": "Hard",
        "level_logo": "https://www.wtatennis.com/resources/v7.42.0/i/elements/1000k-tag.svg",
        "matches": [
            {
                "id": 1,
                "name": "Amanda Anisimova",
                "seed": None,
                "country": "USA",
                "flag": "https://www.wtatennis.com/resources/v7.42.0/i/elements/flags/usa.svg",
                "round": "Round of 64",
                "win_loss": "L",
                "score": "3 - 6,5 - 7,",
                "rank": 41,
                "url_profile": "https://www.wtatennis.com/players/326384/amanda-anisimova",
                "retired": False,
                "walkover": False,
                "bye": False,
                "first_set_tiebreak": False,
                "second_set_tiebreak": False,
                "third_set_tiebreak": False,
                "splitted_score": [
                    [
                        3,
                        6,
                        None
                    ],
                    [
                        5,
                        7,
                        None
                    ]
                ],
                "number_of_sets": 2,
                "first_set_won": False,
                "code_alpha_2": "US",
                "code_alpha_3": "USA",
                "country_code_m49": "840",
                "region_code": "019",
                "region": "America",
                "subregion": "Northern America",
                "fifa": "USA"
            }
        ],
        "start_date": "2025-02-09",
        "end_date": "2025-02-15",
        "year": 2025,
        "month": 2,
        "city": "Doha",
        "country": "Qat",
        "state": None,
        "code_alpha_2": "QA",
        "code_alpha_3": "QAT",
        "country_code_m49": "634",
        "region_code": "142",
        "region": "Asia",
        "subregion": "Western Asia",
        "fifa": "QAT",
        "rank": 30,
        "points_gain": 10,
        "prize_money": 16900,
        "draw": "64M/32Q/32D"
    }
]


def test_player_model():
    for case in TEST_CASES:
        player = PlayerModel(**case)
        assert player.id == case["id"]
        assert player.title == case["title"]
        assert player.logo == case["logo"]
        assert player.url == case["url"]
        assert player.level == case["level"]
        assert player.surface == case["surface"]
        assert player.level_logo == case["level_logo"]
        assert len(player.matches) == len(case["matches"])
