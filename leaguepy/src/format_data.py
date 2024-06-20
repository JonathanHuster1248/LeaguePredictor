import json
import logging
import logging.config
import pandas as pd
import numpy as np
from abc import ABC
from abc import abstractmethod

from pathlib import Path

from leaguepy.src.constants import (
    DEFAULT_LOGGER_CONFIG,
    TeamNumbers,
    PLAYER_TEAM_MAP,
    GAME_DURATION,
)

# We'll want to consider several things eventually, cs, gold/gold per min, objectives, KDA (by member), etc. . However, these data aren't logged cumulatively, so we'll need to pull these out

logging.config.dictConfig(DEFAULT_LOGGER_CONFIG)
logger = logging.getLogger(__name__)


def get_winner(game: dict[str, dict]) -> int:
    """
    return the winning team of a game from a dict of the game

    :param game: a dictionary of metadata and events in a game
    :return: either 100 or 200 to indicate the winning team
    """
    return game["info"]["frames"][-1]["events"][-1]["winningTeam"]


class DataAggregator(ABC):
    @abstractmethod
    def format_json(raw_data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
        pass


class DummyData(DataAggregator):

    col_names = ["something", "other"]

    @staticmethod
    def make_dummy_data(n: int = 10_000) -> pd.DataFrame:
        data = np.random.randint(0, 100, (n, len(DummyData.col_names)))
        df = pd.DataFrame(columns=DummyData.col_names, data=data)
        return df

    @staticmethod
    def format_json(raw_data: dict) -> tuple[pd.DataFrame, np.ndarray]:
        data = DummyData.make_dummy_data()
        wins = np.random.choice(2, len(data))
        return data, wins


class TeamAggregator(DataAggregator):
    # TODO: Make these into a single dict that maps all these attributes to avoid
    # duplicate rows for naming
    index = ["game_id", "timestamp"]
    standard_values = {
        "cs": {  # Could instead normalize to CS per minute
            "norm_val": 10 * 30 * 5,  # 10 CS per minute * 30 minute games * 5 team members
            "pre_agg": True,
            "event_map": None,
        },
        "gold": {
            "norm_val": 3000 * 5,  # Average cost per item * team members
            "pre_agg": True,
            "event_map": None,
        },
        "tower": {
            "norm_val": 8,  # 11 towers in total, but not all need to be taken
            "pre_agg": False,
            "event_map": {
                "event_type": "BUILDING_KILL",
                "event_name": "TOWER_BUILDING",
            },
        },
        "inhibitor": {
            "norm_val": 3,  # 3 Inhibitors in total
            "pre_agg": False,
            "event_map": {
                "event_type": "BUILDING_KILL",
                "event_name": "INHIBITOR_BUILDING",
            },
        },
        "dragon": {
            "norm_val": 4,  # At 4 dragons a team gets soul, which is normal
            "pre_agg": False,
            "event_map": {
                "event_type": "ELITE_MONSTER_KILL",
                "event_name": "DRAGON",
            },
        },
        "riftherald": {
            "norm_val": 1,  # There's only one rift now
            "pre_agg": False,
            "event_map": {
                "event_type": "ELITE_MONSTER_KILL",
                "event_name": "RIFTHERALD",
            },
        },
        "baron": {
            "norm_val": 1,  # Usually only one to two barons are taken
            "pre_agg": False,
            "event_map": {
                "event_type": "ELITE_MONSTER_KILL",
                "event_name": "BARON_NASHOR",
            },
        },
        "elder": {
            "norm_val": 1,  # Usually only one elder dragon is taken
            "pre_agg": False,
            "event_map": {
                "event_type": "ELITE_MONSTER_KILL",
                "event_name": "ELDER_DRAGON",
            },
        },
        "kills": {
            "norm_val": 15,
            "pre_agg": False,
            "event_map": {
                "event_type": "CHAMPION_KILL",
                "event_name": "killerId",
            },
        },
        "assists": {
            "norm_val": 39,
            "pre_agg": False,
            "event_map": {
                "event_type": "CHAMPION_KILL",
                "event_name": "assistingParticipantIds",
            },
        },
        "deaths": {
            "norm_val": 15,
            "pre_agg": False,
            "event_map": {
                "event_type": "CHAMPION_KILL",
                "event_name": "victimId",
            },
        },
    }

    columns = list(standard_values.keys())
    team_columns = [f"{col}_{team}" for col in standard_values for team in TeamNumbers]
    cum_columns = [
        f"{col}_{team}"
        for col, params in standard_values.items()
        for team in TeamNumbers
        if not params["pre_agg"]
    ]
    multi_index = pd.MultiIndex.from_tuples([], names=index)

    event_map = dict()
    for key, value in standard_values.items():
        if not value.get("event_map"):
            continue
        event_type = value["event_map"]["event_type"]
        event_name = value["event_map"]["event_name"]
        if event_map.get(event_type):
            event_map[event_type][event_name] = key
        else:
            event_map[event_type] = {event_name: key}

    def __init__(self) -> None:
        self.df = pd.DataFrame(
            columns=TeamAggregator.team_columns, index=TeamAggregator.multi_index
        )
        self.outcomes = pd.Series(index=TeamAggregator.multi_index)
        super().__init__()

    @staticmethod
    def process_player_frame(player_frame: dict[str, float]) -> pd.Series:
        team = PLAYER_TEAM_MAP[player_frame["participantId"]]
        cs = f"cs_{team}"
        gold = f"gold_{team}"
        player_addition = pd.Series()
        player_addition.loc[cs] = (
            player_frame["jungleMinionsKilled"] + player_frame["minionsKilled"]
        )
        player_addition.loc[gold] = player_frame["totalGold"]
        # TODO: XP could be added here, but likely won't be a driving factor until there is a sizeable xp diff
        # Would maybe be easier to do with just lv difference, but at a minute scale it would be hard
        # To catch the difference
        return player_addition

    @staticmethod
    def process_event_frame(event: dict[str, str | list | int]) -> pd.Series:
        event_frame = pd.Series()
        event_type = event["type"]
        if event_type not in TeamAggregator.event_map:
            return event_frame
        try:
            team = event["teamId"] if "teamId" in event else PLAYER_TEAM_MAP[event["killerId"]]
        except KeyError:
            # Event not affiliated with a team. Skip to next
            return event_frame

        # CONTINUE HERE
        if event_type == "ELITE_MONSTER_KILL":
            monster = TeamAggregator.event_map[event_type][event["monsterType"]]
            event_frame.loc[f"{monster}_{team}"] = 1
        if event_type == "BUILDING_KILL":
            monster = TeamAggregator.event_map[event_type][event["buildingType"]]
            event_frame.loc[f"{monster}_{team}"] = 1
        if event_type == "CHAMPION_KILL":
            killed_team = PLAYER_TEAM_MAP[event["victimId"]]
            if killed_team == team:
                logger.warning(
                    "Data found where one team member killed another team member. If Renatta Glasc is not involved, I don't know what happened"
                )
            # assert killed_team != team

            event_frame.loc[f"kills_{team}"] = 1
            event_frame.loc[f"assists_{team}"] = len(event.get("assistingParticipantIds", []))
            event_frame.loc[f"deaths_{killed_team}"] = 1
        return event_frame

    @staticmethod
    def add_frame(frame: dict) -> pd.Series:
        events = frame.get("events") or []
        player_frames = frame.get("participantFrames") or {}

        frame_series = pd.Series(data=0, index=TeamAggregator.team_columns)

        # Add data from player snapshots
        for player in player_frames.values():
            player_snapshot = TeamAggregator.process_player_frame(player)
            frame_series = frame_series.add(player_snapshot, fill_value=0)
        # Add data from event snapshots
        for event in events:
            event_frame = TeamAggregator.process_event_frame(event)
            frame_series = frame_series.add(event_frame, fill_value=0)
        return frame_series

    @staticmethod
    def format_game(game: dict[str, dict]) -> tuple[pd.DataFrame, pd.Series]:

        game_df = pd.DataFrame(
            columns=TeamAggregator.team_columns, index=TeamAggregator.multi_index
        )
        outcomes = pd.Series(index=TeamAggregator.multi_index)

        game_id = game["info"]["gameId"]
        frames = game["info"]["frames"]

        winner = get_winner(game)
        second_half_frames = frames[int(len(frames) / 2) :]
        for frame in second_half_frames:
            # Normalize the timestamp here since it is also the index and would be difficult to
            # modify later
            idx = (game_id, frame["timestamp"] / GAME_DURATION)
            game_df.loc[idx, :] = TeamAggregator.add_frame(frame)
            outcomes.loc[idx, "outcome"] = winner / TeamNumbers.TEAM1 - 1
        game_df.loc[:, TeamAggregator.cum_columns] = game_df.loc[:, TeamAggregator.cum_columns].agg(
            "cumsum"
        )
        return game_df, outcomes

    def format_json(self, raw_data: dict[str, dict]) -> None:
        games_list = []
        outcomes_list = []
        for game in raw_data.values():
            try:
                game_df, outcomes = self.format_game(game)
            except KeyError:
                # The format of the game was malformed (eg we got a message in our json instead of a game)
                continue
            games_list.append(game_df)
            outcomes_list.append(outcomes)
        self.df = pd.concat([self.df] + games_list)
        self.outcomes = pd.concat([self.outcomes] + outcomes_list)

    @staticmethod
    def normalize(df):
        vals = np.repeat(
            [param["norm_val"] for param in TeamAggregator.standard_values.values()],
            len(TeamNumbers),
        )
        data = dict(zip(TeamAggregator.team_columns, vals))
        normalizer = pd.DataFrame(data, index=df.index, columns=TeamAggregator.team_columns)

        return df.div(normalizer)

    def prepare_train(self) -> tuple[np.ndarray, np.ndarray]:
        normalized_df = self.normalize(self.df)
        X = normalized_df.reset_index().drop("game_id", axis=1).values
        y = self.outcomes.values.astype(int)
        return X, y


class RoleAggregator(DataAggregator):
    pass


class PlayerAggregator(DataAggregator):
    pass


# Format data, should take an algorithm and a file output type
#   Types: (These should be a class with a process_data method)
#       - Team Aggregation
#       - Role Aggregation
#       - Player/Champion Aggregation

if __name__ == "__main__":
    DIR = Path(
        r"C:\Users\jonhuster\Desktop\General\Personal\Projects\Python\LeaguePredictor\data\raw"
    )
    model = TeamAggregator()
    for j in range(3):
        with open(DIR / f"faker_norms_data_{j}.json") as json_file:
            data = json.load(json_file)
        model.format_json(data)
        model.normalize()
        # write_games(data, out_dir=DIR.parent / "matches")
