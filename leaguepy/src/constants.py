import os
import numpy as np

from datetime import datetime
from dotenv import load_dotenv
from enum import Enum, IntEnum


# =====================LOGGING CONSTANTS=======================
now = datetime.now()
# Define the logging configuration dictionary
DEFAULT_LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(name)s - %(asctime)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "file_handler": {
            "class": "logging.FileHandler",
            "filename": f'LeaguePy_{now.strftime("%Y-%m-%d-%H-%M-%S")}.log',
            "encoding": "utf8",
            "formatter": "default",
        },
        "stream_handler": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["file_handler", "stream_handler"],
        "level": "DEBUG",
    },
}

# ===================RIOT API CONSTANTS===========================

load_dotenv()
# To generate a key go to this web address, make an account, and regenerate a developement api key
# https://developer.riotgames.com/
API_KEY = os.getenv("RIOT_API_KEY")


RIOT_PARAMS = {
    # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    # "Accept-Language": "en-US,en;q=0.9",
    # "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    # "Origin": "https://developer.riotgames.com",
    # "X-Riot-Token": f"{API_KEY}",
    "api_key": f"{API_KEY}",
}


class Region(str, Enum):
    AMERICAS = "americas"
    ASIA = "asia"
    EUROPE = "europe"
    SEA = "sea"


class Country(str, Enum):
    KOREA = "kr"
    EUROPE_NORTH = "EUN1"
    EUROPE_WEST = "EUW1"
    JAPAN = "JP1"
    NORTH_AMERICA = "NA1"


class MatchType(str, Enum):
    NORMAL = "normal"
    RANKED = "ranked"


URLS = {
    "puuid": "https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tagline}",
    "match_hist": "https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type={type}&start={start}&count={count}",
    "timeline": "https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline",
}


# ===================DATA GATHERING CONSTANTS====================
SEED_PUUID = "jmErjfBJ2tBOKgQvAlpwDKqatv7Me7H8_KI5iUkbcszfwMorv_0piifdO0___EMXWgY8b25X-CMY2w"  # PUUID from a player in a game with Faker in it


# ===================DATA PROCESSING CONSTANTS====================

NUMBER_PLAYERS = 10
PLAYERS = range(1, NUMBER_PLAYERS + 1)
GAME_DURATION = 30 * 60 * 1000  # 30 Minutes * Seconds/Min * Miliseconds/second


class TeamNumbers(IntEnum):
    TEAM1 = 100
    TEAM2 = 200


PLAYER_TEAM_MAP = dict(zip(PLAYERS, np.repeat(list(TeamNumbers), 5)))
