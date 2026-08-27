import json
import contextvars
import pandas as pd
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent
from langchain.tools import tool
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.schema import HumanMessage, SystemMessage

from config import get_wyscout_client, POS_GROUPS, DEFAULT_MODEL_NAME
from storage import load_user_data, save_user_data, load_localization, fetch_metrics_csv
from telegram import direct_message, send_menu, send_photo, build_menu_buttons
from database import (
    request_data,
    assemble_seasons,
    aggregate_season,
    calculate_pos,
    get_season_str,
)
from metrics import get_position_metrics, calculate_raws, calculate_ranks
from charts import (
    generate_stat_histogram,
    generate_performance_heatmap,
    generate_position_pie,
)

# ContextVar ensures thread-safe / request-safe chat_id and language per invocation
current_chat_id = contextvars.ContextVar("current_chat_id", default=None)


def get_current_chat_id() -> int:
    cid = current_chat_id.get()
    if cid is None:
        raise ValueError("current_chat_id is not set in this context.")
    return cid


def season_analysis(season: int, pos: str, wyscout_id: int | str, pldocs: pd.DataFrame, season_documents=None):
    """Performs statistical analysis of a player's season and sends natural language evaluation."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json() or {}
    lang = user_data.get('language', 'loc_en')
    locstr = load_localization(lang)

    client = get_wyscout_client()
    stat_df = fetch_metrics_csv()
    totsdf = get_position_metrics(pos, stat_df)
    tots = pd.concat([totsdf['colname'], totsdf['att_colname']], ignore_index=True).unique()
    tots = list(tots[tots != 'empty'])

    def calculate_player(player_id, docs, role):
        fplayerdocs = docs[docs['player_id'] == player_id]
        playerdocs = fplayerdocs[fplayerdocs["player_position"].apply(lambda x: x in POS_GROUPS.get(role, []))]
        mostplayed = playerdocs[playerdocs['mins'] == max(playerdocs['mins'])].iloc[0].copy()
        mostplayed['mins'] = sum(playerdocs['mins'])
        return mostplayed

    if season_documents is None or len(season_documents) == 0:
        season_documents = request_data({'seasonId': int(season)}, ['player_position'] + tots)
    else:
        season_documents = season_documents[['player_position', "player_name", "team_id", "team_name", "player_id", "mins", "90s", "team", "player"] + tots]

    season_documents = pd.DataFrame(season_documents)
    gooddocs = season_documents[season_documents["player_position"].apply(lambda x: x in POS_GROUPS.get(pos, []))]

    if int(wyscout_id) not in list(gooddocs['player_id'].unique()):
        direct_message(chat_id, locstr.get('no_data_this_position', "No data for this position."))
        return

    competition_df = []
    for player in gooddocs['player_id'].unique():
        competition_df.append(calculate_player(player, season_documents, pos))

    competition_df = pd.DataFrame(competition_df)
    mintresh = 900
    comp_df = competition_df[competition_df.mins > mintresh].copy()
    if len(comp_df) <= 8:
        mintresh = max(competition_df.mins) * 0.2
        comp_df = competition_df[competition_df.mins > mintresh]
    if len(comp_df[comp_df['player_id'] == int(wyscout_id)]) == 0:
        comp_df.loc['player'] = competition_df[competition_df['player_id'] == int(wyscout_id)].iloc[0]

    competition_df = comp_df.copy()
    dt = competition_df[competition_df['player_id'] == int(wyscout_id)].iloc[0]

    crdata = pd.DataFrame(client.player_career(wyscout_id)['career'])
    crdata = crdata[crdata['seasonId'] == season].iloc[0]
    player = client.player(int(wyscout_id))

    plshort = {p: player.get(p, '') for p in ['shortName', 'firstName', 'middleName', 'lastName']}
    rawseasdata = get_season_str(season, crdata, client, raw=True)

    selseastext = locstr.get('selseas_0', '') + '\n\n' + locstr.get('selseas_1', '') + '\n\n' + locstr.get('selseas_2', '')
    selseastext = selseastext.format(
        name=player['shortName'], pos=pos, bday=player['birthDate'],
        country=player['birthArea']['name'], season=rawseasdata['season'],
        appearances=rawseasdata['career']['appearances'], team=rawseasdata['team'],
        minutes=rawseasdata['career']['minutesPlayed'],
        goals=int(pldocs['is_goal'].sum()) if 'is_goal' in pldocs.columns else 0,
        assists=int(pldocs['assists'].sum()) if 'assists' in pldocs.columns else 0,
        rminutes=dt['mins']
    )
    direct_message(chat_id, selseastext)

    all_raws = calculate_raws(totsdf, stat_df, competition_df, lang)
    all_ranks = calculate_ranks(totsdf, stat_df, all_raws, lang)
    percentile_ranks = all_ranks.loc[dt.name].to_dict()

    goods, bads, averages = {}, {}, {}
    for i, rank_val in percentile_ranks.items():
        if i not in ['player', 'team', "player_id", "mins"]:
            z = float(rank_val)
            if z <= 40:
                bads[i] = z
            elif z <= 70:
                averages[i] = z
            else:
                goods[i] = z

    phrase = ''
    if len(goods) > 0:
        phrase += f"Metrics indicate he's very strong at: {goods}. "
    else:
        phrase += "Unfortunately, none of his metrics are strong. "
    if len(bads) > 0:
        phrase += f"Metrics indicate he's weak at: {bads}. "
    else:
        phrase += "Fortunately, none of his metrics are weak. "
    if len(bads) == 0 or len(goods) == 0:
        phrase += f"Metrics indicate he's average at: {averages}. "

    plteam = dt['team']['name']
    cllm = ChatOpenAI(model_name=DEFAULT_MODEL_NAME, temperature=0.25)
    ztxt = "You are a football club analyst. When provided player stats, write a thoughtful analysis, adding smart comments outlining interplay between his parameters."
    messages = [
        SystemMessage(content=ztxt),
        HumanMessage(content=f"Here's a player playing as a {pos} in {plteam}. His name is: {plshort}. His metrics: {phrase}.{locstr.get('response_lang', '')}"),
    ]
    z = cllm(messages)
    analysis_text = z.content

    updated_data = {
        'language': lang,
        'wyscoutId': int(wyscout_id),
        'position': pos,
        'season': int(season),
        'data': all_raws.to_dict(),
        'percentiles': percentile_ranks
    }
    save_user_data(chat_id, updated_data)
    direct_message(chat_id, analysis_text)


# ------------------------------------------------------------------------------
# LangChain ReAct Tools
# ------------------------------------------------------------------------------
@tool("get_wyscout_id", return_direct=False)
def tool_get_wyscout_id(transfermarkt_url: str) -> str:
    """Takes a transfermarkt URL provided by user and finds the player's wyscout_id in the wyscout database."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json() or {}
    llm = ChatOpenAI(model_name=DEFAULT_MODEL_NAME, temperature=0)
    search = GoogleSerperAPIWrapper()
    search_data = search.results(transfermarkt_url)['organic'][0]
    messages = [
        SystemMessage(content="You are an assistant who reformats and returns data in the following format: ***Name,Birth Date***. Example: ***Niki Kozh,05/05/2005***"),
        HumanMessage(content=f"Here's data: ***{search_data}***"),
    ]
    z = llm(messages).content.replace("\n", '')

    client = get_wyscout_client()
    nme = z.split(',')[0].split(' ')
    dsdata = client.search(nme[0] + ' ' + nme[-1], "player")[:10]
    messages = [
        SystemMessage(content=f"You are an assistant who returns the wyId of the player from the provided list, who best fits this data: {z}. Respond with integer only, no spaces or symbols."),
        HumanMessage(content=f"Here's data: ***{dsdata}***. Respond with wyId only, no text or special symbols."),
    ]
    wyid = llm(messages).content.replace("\n", '')

    user_data['wyscoutId'] = int(wyid)
    save_user_data(chat_id, user_data)
    return f"wyscout_id: {int(wyid)}. Provide it to following functions as an integer, without any prefixes or text."


@tool("get_player_career", return_direct=True)
def tool_get_player_career(wyscout_id: str) -> str:
    """Returns the player's verbal career analysis through the wyscout database."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json() or {}
    locstr = load_localization(user_data.get('language', 'loc_en'))
    client = get_wyscout_client()

    clean_id = ''.join(c for c in wyscout_id if c.isdigit())
    pldocs, season, seastext, slabels, sids = assemble_seasons(clean_id, client, locstr)
    if season == 0:
        direct_message(chat_id, locstr.get('not_enough_data', "Not enough data available."))
        return {'statusCode': 200}

    menu = build_menu_buttons(slabels, sids)
    send_menu(chat_id, seastext, menu)
    return {'statusCode': 200}


@tool("get_current_data", return_direct=True)
def tool_get_current_data(any_input: str = '') -> str:
    """Looks up currently stored player data."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json()
    if not user_data or 'wyscoutId' not in user_data:
        locstr = load_localization('loc_en')
        direct_message(chat_id, locstr.get('no_data_stored', "No data stored."))
        return

    locstr = load_localization(user_data.get('language', 'loc_en'))
    client = get_wyscout_client()
    player = client.player(user_data['wyscoutId'])
    out = locstr.get('stored_player', '')

    if 'season' in user_data:
        sdata = client.season(user_data['season'])
        comp = client.competition(sdata['competitionId'])
        out += locstr.get('stored_season', '')
        out = out.format(
            name=player['shortName'], id=user_data['wyscoutId'],
            sname=sdata['name'], cname=comp['name'], cformat=comp['format'], caname=comp['area']['name']
        )
    else:
        out += locstr.get('no_stored_season', '')
        out = out.format(name=player['shortName'], id=user_data['wyscoutId'])

    direct_message(chat_id, out)
    return {'statusCode': 200}


@tool("plot_stat_breakdown", return_direct=True)
def tool_plot_stat_breakdown(metric: str) -> str:
    """Takes a metric name and plots a chart."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json()
    if not user_data or 'data' not in user_data:
        return "Failed to retrieve data."

    locstr = load_localization(user_data.get('language', 'loc_en'))
    data = pd.DataFrame(user_data['data'])
    llm = ChatOpenAI(model_name=DEFAULT_MODEL_NAME, temperature=0)
    messages = [
        SystemMessage(content=f"Return the one that is most likely to be {metric}, with no extra symbols. Keep the formatting from the list. If it's not in the list of columns, return ***None***."),
        HumanMessage(content=f"Here's a list of columns: ***{list(data.columns)}***."),
    ]
    resolved_metric = llm(messages).content.replace('\n', '').strip()
    if 'None' in resolved_metric or resolved_metric not in data.columns:
        direct_message(chat_id, locstr.get('no_metric', "Metric not found."))
        return {'statusCode': 200}

    buf = generate_stat_histogram(user_data, resolved_metric, locstr)
    if buf:
        send_photo(chat_id, buf, "histogram.jpg")
    return {'statusCode': 200}


@tool("show_player_performance", return_direct=True)
def tool_show_player_performance(anytext: str) -> str:
    """Shows player's personal performance table heatmap."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json()
    if not user_data:
        return "Failed to retrieve data."
    buf = generate_performance_heatmap(user_data)
    if buf:
        send_photo(chat_id, buf, "performance.jpg")
    return {'statusCode': 200}


@tool("get_specific_season", return_direct=True)
def tool_get_specific_season(season_id: str) -> str:
    """Shows player's data for a requested season."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json()
    if not user_data:
        return "Failed to retrieve data."

    locstr = load_localization(user_data.get('language', 'loc_en'))
    client = get_wyscout_client()
    wyscout_id = user_data['wyscoutId']
    pldocs, _, _, _, _ = assemble_seasons(wyscout_id, client, locstr)
    season = int(season_id)

    pldocs = pldocs[pldocs['seasonId'] == season] if len(pldocs) > 0 else pd.DataFrame()
    alldocs = None
    if len(pldocs) == 0:
        alldocs = aggregate_season(season, chat_id, locstr)
        if len(alldocs) == 0:
            return {'statusCode': 200}
        pldocs = alldocs[alldocs['player_id'] == wyscout_id]

    pos = calculate_pos(pldocs)
    season_analysis(season, pos, wyscout_id, pldocs, alldocs)
    return {'statusCode': 200}


@tool("get_season_by_id", return_direct=True)
def tool_get_season_by_id(season_id: str) -> str:
    """Shows player's data for a requested season by season_id."""
    clean_id = ''.join(c for c in season_id if c.isdigit())
    return tool_get_specific_season(clean_id)


@tool("get_specific_position", return_direct=True)
def tool_get_specific_position(position_info: str) -> str:
    """Obtains and shows player's data for a requested position."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json()
    if not user_data:
        return "Failed to retrieve data."

    locstr = load_localization(user_data.get('language', 'loc_en'))
    client = get_wyscout_client()
    wyscout_id = user_data['wyscoutId']
    season = user_data.get('season')
    pldocs, _, _, _, _ = assemble_seasons(wyscout_id, client, locstr)

    llm = ChatOpenAI(model_name=DEFAULT_MODEL_NAME, temperature=0)
    messages = [
        SystemMessage(content="You will be provided with an original list of existing player positions. Identify the position most likely to fit the request. Respond with the position name identically."),
        HumanMessage(content=f"List of positions: {list(POS_GROUPS.keys())}. Fit: {position_info}"),
    ]
    pos = llm(messages).content.replace('\n', '').strip()
    pldocs = pldocs[pldocs['seasonId'] == season] if len(pldocs) > 0 else pd.DataFrame()
    season_analysis(season, pos, wyscout_id, pldocs)
    return {'statusCode': 200}


@tool("show_player_positions", return_direct=True)
def tool_show_player_positions(request: str) -> str:
    """Finds and shows positions the player played in."""
    chat_id = get_current_chat_id()
    user_data = load_user_data(chat_id).json()
    if not user_data:
        return "Failed to retrieve data."

    locstr = load_localization(user_data.get('language', 'loc_en'))
    client = get_wyscout_client()
    wyscout_id = user_data['wyscoutId']
    season = int(user_data.get('season', 0))
    pldocs, _, _, _, _ = assemble_seasons(wyscout_id, client, locstr)

    pldocs = pldocs[pldocs['seasonId'] == season] if len(pldocs) > 0 else pd.DataFrame()
    buf = generate_position_pie(user_data, pldocs)
    if buf:
        send_photo(chat_id, buf, "positions.jpg")
    return {'statusCode': 200}


# Registered tool list
SCOUTING_TOOLS = [
    tool_get_wyscout_id,
    tool_get_player_career,
    tool_plot_stat_breakdown,
    tool_show_player_performance,
    tool_get_specific_season,
    tool_get_season_by_id,
    tool_get_specific_position,
    tool_show_player_positions,
    tool_get_current_data
]


def run_scouting_agent(prompt_text: str, chat_id: int):
    """Initializes and runs the scouting LangChain agent for a user query."""
    token = current_chat_id.set(chat_id)
    try:
        llm = OpenAI(model_name=DEFAULT_MODEL_NAME, temperature=0)
        agent = initialize_agent(
            SCOUTING_TOOLS,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        return agent.run(prompt_text)
    finally:
        current_chat_id.reset(token)
