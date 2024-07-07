import json
import logging
import logging.config
import requests
import time
from functools import wraps
from pathlib import Path
from requests.exceptions import HTTPError

from leaguepy.src.constants import (
    Region,
    MatchType,
    URLS,
    RIOT_PARAMS,
    DEFAULT_LOGGER_CONFIG,
)

# TODO: There should be a wrapper function for exponential wait (with cutoff) for these API calls

logging.config.dictConfig(DEFAULT_LOGGER_CONFIG)
logger = logging.getLogger(__name__)

# 20 requests/second and 100 requests/120 seconds
DEFAULT_WAIT = 60  # Seconds


def retry_on_rate_limit(retry_wait_time=DEFAULT_WAIT):
    """
    Decorator that retries the function if an API rate limit (HTTP 429) is encountered.

    Args:
    - retry_wait_time (int): The time to wait before retrying if the API rate limit is exceeded (in seconds).

    Returns:
    - Decorated function with retry logic.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            while True:
                try:
                    response = func(*args, **kwargs)
                    response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx, 5xx)
                    return response
                except HTTPError as http_err:
                    if http_err.response.status_code == 429:
                        logger.warning(
                            f"Rate limit exceeded. Retrying in {retry_wait_time} seconds..."
                        )
                        time.sleep(retry_wait_time)
                    else:
                        raise http_err

        return wrapper

    return decorator


def write_if_not_none(data, filename: Path | None = None) -> None:
    if data is not None:
        with open(filename, "w", encoding="utf8") as outfile:
            json.dump(data, outfile)


# This function is relatively less useful now that the endpoint requries both the username and the
# tag, which is hard to get, so instead use function gather_puuid_from_seed to get a list of
# PUUIDs to iterate over.
@retry_on_rate_limit()
def pull_puuid(username: str, tagline: str, region: Region = Region.ASIA) -> requests.Response:
    URL = URLS["puuid"]
    response = requests.get(
        URL.format(region=region.value, username=username, tagline=tagline), params=RIOT_PARAMS
    )
    logger.info(f"PUUID Retrieval Status Code: {response.status_code}")
    return response


@retry_on_rate_limit()
def get_match_history(
    puuid: str,
    region: Region = Region.ASIA,
    type: MatchType = MatchType.NORMAL,
    start: int = 0,
    count: int = 20,
) -> requests.Response:
    URL = URLS["match_hist"]
    logger.info(f"Pulling match history for puuid: {puuid}")
    response = requests.get(
        URL.format(region=region, puuid=puuid, type=type, start=start, count=count),
        params=RIOT_PARAMS,
    )
    return response


@retry_on_rate_limit()
def get_timeline(match_id: str, region: Region = Region.ASIA) -> requests.Response:
    # data return structure
    # - 'metadata'
    #     - 'dataVersion'
    #         - str (int)
    #     - 'matchId'
    #         - str
    #     - 'participants'
    #         - set[str]
    # - 'info'
    #     - 'frameInterval'
    #         -int # probably ms
    #     - 'frames'
    #         - list
    #             - 'events'
    #             - 'participantFrames'
    #                 - ['participantid']
    #                     - 'championStats'
    #                         - 'abilityHaste'
    #                         - 'abilityPower'
    #                         - 'armor'
    #                         - 'armorPen'
    #                         - 'armorPenPercent'
    #                         - 'attackDamage'
    #                         - 'attackSpeed'
    #                         - 'bonusArmorPenPercent'
    #                         - 'bonusMagicPenPercent'
    #                         - 'ccReduction'
    #                         - 'cooldownReduction'
    #                         - 'health'
    #                         - 'healthMax'
    #                         - 'healthRegen'
    #                         - 'lifesteal'
    #                         - 'magicPen'
    #                         - 'magicPenPercent'
    #                         - 'magicResist'
    #                         - 'movementSpeed'
    #                         - 'omnivamp'
    #                         - 'physicalVamp'
    #                         - 'power'
    #                         - 'powerMax'
    #                         - 'powerRegen'
    #                         - 'spellVamp'
    #                     - 'currentGold'
    #                         - int
    #                     - 'damageStats'
    #                         - 'magicDamageDone'
    #                         - 'magicDamageDoneToChampions'
    #                         - 'magicDamageTaken'
    #                         - 'physicalDamageDone'
    #                         - 'physicalDamageDoneToChampions'
    #                         - 'physicalDamageTaken'
    #                         - 'totalDamageDone'
    #                         - 'totalDamageDoneToChampions'
    #                         - 'totalDamageTaken'
    #                         - 'trueDamageDone'
    #                         - 'trueDamageDoneToChampions'
    #                         - 'trueDamageTaken'
    #                     - 'goldPerSecond'
    #                         - int
    #                     - 'jungleMinionsKilled'
    #                         - int
    #                     - 'level'
    #                         - int
    #                     - 'minionsKilled'
    #                         - int
    #                     - 'participantId'
    #                         - int
    #                     - 'position'
    #                         - 'x' int
    #                         - 'y' int
    #                     - 'timeEnemySpentControlled'
    #                         - int
    #                     - 'totalGold'
    #                         - int
    #                     - 'xp
    #                         - int
    #             - 'timestamp'
    #                 -int
    #     - 'gameId'
    #         - int
    #     - 'participants'
    #         - dict[int, str]

    URL = URLS["timeline"]
    logger.info(f"Pulling timeline for match_id: {match_id}")
    response = requests.get(URL.format(region=region.value, match_id=match_id), params=RIOT_PARAMS)
    return response


def get_player_ids(match: dict[str, dict]) -> set[str]:
    return set(match.get("metadata", {}).get("participants", {}))


def get_puuid_options(seed_puuid: str, seed_region: Region, depth: int = 5) -> set[str]:
    if depth == 0:
        return set(seed_puuid)

    puuid_options = set()

    match_history = get_match_history(seed_puuid, region=seed_region, count=depth).json()
    for match_id in match_history:
        match_data = get_timeline(match_id, region=seed_region).json()
        puuid_options = puuid_options.union(get_player_ids(match_data))
        # TODO: this ignores the correlation between players (eg we know that all 10 players from the
        # most recent game will be searched )
    for puuid in puuid_options:
        if puuid == seed_puuid:
            continue
        additional_puuids = get_puuid_options(puuid, seed_region, depth - 1)
        puuid_options = puuid_options.union(additional_puuids)

    return puuid_options


def get_game_history(
    puuid: str,
    region: Region = Region.ASIA,
    **args,
) -> dict:
    """This function takes a username and pulls the time series for their last 20 games and puts it into a json

    Args:
        username (str): The username of the person you would like to search
        country (Country, optional): The country of the player in question. Defaults to Country.korea.
        region (Region, optional): The region of the player in question. Defaults to Region.asia.
        filename (str, optional): The output path if desired. Defaults to None.

    Returns:
        dict: a dictionary of timeseries of (up to) the last 20 games
    """
    match_history = get_match_history(puuid, region=region, **args).json()
    timeseries = dict()
    for i, match in enumerate(match_history):
        timeseries[i] = get_timeline(match, region=region).json()

    return timeseries


# TODO: This code doesn't have a way of systematically retrieving different data. right now if we ran get_game_history it would grab 20 games and forever grab the same games. We need a way to systematically grab other data for the same players
if __name__ == "__main__":

    DIR = Path(
        r"C:\Users\jonhuster\Desktop\General\Personal\Projects\Python\LeaguePredictor\leaguepy\data\raw"
    )
    for i in range(20):
        game_history = get_game_history(
            "isthisaward",
            "NA1",
            region=Region.AMERICAS,
            type=MatchType.NORMAL,
            start=i * 100,
            count=100,
        )
        write_if_not_none(game_history, DIR / f"personal_norms_data_v2_{i}.json")
