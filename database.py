import pandas as pd
from pymongo import MongoClient
from config import (
    MONGO_USERNAME,
    MONGO_PASSWORD,
    MONGO_HOST,
    MONGO_DATABASE,
    POS_GROUPS,
)
from telegram import direct_message

_mongo_client = None


def get_mongo_db():
    """Initializes and returns the singleton MongoDB database instance."""
    global _mongo_client
    if _mongo_client is None:
        if MONGO_USERNAME and MONGO_PASSWORD:
            uri = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}"
        else:
            uri = f"mongodb://{MONGO_HOST}"
        _mongo_client = MongoClient(uri)
    return _mongo_client[MONGO_DATABASE]


def get_collection(name: str = "player_season_aggregated_stats"):
    db = get_mongo_db()
    return db[name]


def request_data(filters: dict = None, fields: list[str] = None, collection=None, all_fields: bool = False) -> list[dict]:
    """Queries MongoDB using an aggregation pipeline to extract player stats."""
    if filters is None:
        filters = {}
    if fields is None:
        fields = []
    if collection is None:
        collection = get_collection()

    pipeline = [
        {
            "$addFields": {
                "player_id": {"$getField": {"field": "player.id", "input": "$$ROOT"}},
                "player_name": {"$getField": {"field": "player.name", "input": "$$ROOT"}},
                "team_id": {"$getField": {"field": "team.id", "input": "$$ROOT"}},
                "team_name": {"$getField": {"field": "team.name", "input": "$$ROOT"}},
                "player_position": {"$getField": {"field": "player.position", "input": "$$ROOT"}},
                "shot_postShotXg": {"$getField": {"field": "shot.postShotXg", "input": "$$ROOT"}},
                "carry_fields_gained": {"$getField": {"field": "carry.fields_gained", "input": "$$ROOT"}}
            }
        }
    ]

    if len(filters) > 0:
        pipeline.append({"$match": filters})
    else:
        pass

    if not all_fields:
        flds = {
            "$project": {
                "player.id": "$player_id",
                "player.name": "$player_name",
                "team.id": "$team_id",
                "team.name": "$team_name",
                "player.position": "$player_position",
                "player_id": 1,
                "mins": 1,
                "90s": 1,
            }
        }
        for field in fields:
            flds["$project"][field] = 1
        pipeline.append(flds)

    return list(collection.aggregate(pipeline))


def aggregate_season(season_id: int, chat_id: int, locstr: dict) -> pd.DataFrame:
    """Aggregates player match stats for a specific season."""
    db = get_mongo_db()
    scol = db["player_match_stats"]
    documents = request_data({'seasonId': int(season_id)}, [], scol, all_fields=True)

    if len(documents) == 0:
        direct_message(chat_id, locstr.get('no_data_this_season', "No data for this season."))
        return pd.DataFrame()
    else:
        df = pd.DataFrame(documents)
        player_df_list = [pd.DataFrame(row['players']) for _, row in df.iterrows()]
        all_players_df = pd.concat(player_df_list, ignore_index=True)

        agg_lib = {
            'shirtNumber': 'first',
            'team_id': 'first',
            'player_position': 'first',
            'matchId': 'first',
            'player_id': 'first',
            'player_name': 'first',
            'team_name': 'first'
        }

        all_players_df = all_players_df.rename(columns={
            "player.id": "player_id",
            "player.name": "player_name",
            "team.id": "team_id",
            "team.name": "team_name",
            "player.position": "player_position",
            "carry.fields_gained": "carry_fields_gained",
            "shot.postShotXg_gk": "shot_postShotXg"
        })

        for col in all_players_df.columns:
            if col not in agg_lib:
                agg_lib[col] = 'sum'

        all_players_df = all_players_df[list(agg_lib.keys())].copy()
        duplicates = all_players_df.columns.duplicated()
        all_players_df = all_players_df.loc[:, ~duplicates]

        for card_col in ['yellowCards', 'redCards']:
            if card_col in all_players_df.columns:
                all_players_df[card_col] = all_players_df[card_col].apply(lambda x: int(x) if pd.notnull(x) else 0)

        aggregated_df = all_players_df.groupby(['player_id', 'player_position']).agg(agg_lib).reset_index(drop=True)
        aggregated_df['player'] = aggregated_df['player_position'].apply(lambda x: {'position': x})
        aggregated_df['team'] = aggregated_df.apply(lambda x: {'name': x['team_name'], 'id': x['team_id']}, axis=1)
        aggregated_df['90s'] = aggregated_df['mins'] / 90
        return aggregated_df


def get_season_str(season_id: int, career_data: dict, client, raw: bool = False, long: bool = True):
    """Formats season information string or dictionary."""
    ssn = client.season(season_id)
    team = client.team(career_data['teamId'])
    competition = client.competition(ssn['competitionId'])
    if raw:
        return {
            'season': f"{competition['name']}({competition['area']['name']}) season of {ssn['name']}",
            'career': career_data,
            'team': team['name']
        }
    elif long:
        return (
            f"{competition['name']}({competition['area']['name']}) season of {ssn['name']}, "
            f"minutes played: {career_data['minutesPlayed']}, for {team['name']}. Season wyscout id: {season_id}."
        )
    else:
        return f"{competition['name']}({competition['area']['name']}),{ssn['name']}, {career_data['minutesPlayed']} mins, {team['name']}"


def assemble_seasons(wyscout_id: str | int, client, locstr: dict):
    """Retrieves player documents and builds formatted season choices."""
    documents = request_data({'player_id': int(wyscout_id)}, ['seasonId', 'is_goal', 'assists'])
    pldocs = pd.DataFrame(documents)
    if len(pldocs) == 0:
        print("No player data in our database.")
        return [], 0, '', [], []

    seasons = pldocs['seasonId'].unique()
    career = client.player_career(wyscout_id)['career']
    career.reverse()

    treshold = 500
    season = 0
    seastext = locstr.get('av_seasons_0', '')
    extraseastext = locstr.get('av_seasons_1', '')
    j = 1
    k = 1
    slabels = []
    sids = []

    for i in career:
        if i['minutesPlayed'] > treshold:
            if i['seasonId'] in seasons:
                s = i['seasonId']
                seastext += f'\n{j}) '
                j += 1
                seastext += get_season_str(s, i, client)
                seastext += '\n'
                slabels.append(get_season_str(s, i, client, raw=False, long=False))
                sids.append(f's{s}')
                if season == 0:
                    season = i['seasonId']
            elif k <= 3:
                s = i['seasonId']
                extraseastext += f'\n{k}) '
                k += 1
                extraseastext += get_season_str(s, i, client)
                extraseastext += '\n'
                slabels.append(get_season_str(s, i, client, raw=False, long=False))
                sids.append(f's{s}')

    return pldocs, season, seastext + extraseastext + locstr.get('av_seasons_2', ''), slabels, sids


def calculate_pos(pldocs: pd.DataFrame) -> str | None:
    """Finds the most played position name for a player based on minutes."""
    pos = None
    time = 0
    for key, positions in POS_GROUPS.items():
        postime = pldocs[pldocs['player'].apply(lambda x: x.get('position') in positions if isinstance(x, dict) else False)]
        total_mins = sum(postime['mins']) if 'mins' in postime else 0
        if total_mins > time:
            time = total_mins
            pos = key
    return pos
