import io
import requests
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import Normalize
import seaborn as sns
from PIL import Image
from config import get_wyscout_client, POS_GROUPS
from storage import fetch_metrics_dicts, fetch_metrics_csv


def generate_player_card(user_data: dict, locstr: dict) -> io.BytesIO | None:
    """Generates the player radar/bar percentile card visual."""
    client = get_wyscout_client()

    def clear_percentiles(data):
        return dict([(key, val) for key, val in data.items() if key not in ['player', 'team', 'player_id', 'mins']])

    try:
        player_metrics = clear_percentiles(user_data['percentiles'])
        player = client.player(user_data['wyscoutId'])
        player_name = player['shortName']
        player_position = user_data['position']
        player_pic = player['imageDataURL']
        team = client.team(user_data['percentiles']['team']['id'])
        team_name = team['officialName']
        team_pic = team['imageDataURL']
        season = client.season(user_data['season'])
        competition = client.competition(season['competitionId'])
        season_name = f"{competition['name']}({competition['area']['name']}) {locstr.get('season_of', 'season of')} {season['name']}"
    except Exception as ex:
        print(f"Error fetching data for player card: {ex}")
        return None

    linecolor = '#BAE2FF'
    facecolor = '#001728'
    bgcolor = '#002F51'

    labels = list(player_metrics.keys())
    values = list(player_metrics.values())

    data_list = fetch_metrics_dicts()
    remap_dict = {}
    if data_list and len(data_list) > 8:
        for row in range(1, len(data_list[0])):
            loc_en = list(data_list[7].keys())[row]
            loc_en = data_list[7][loc_en]
            loc_ru = list(data_list[7].keys())[row]
            loc_ru = data_list[8][loc_ru]
            rank_type = list(data_list[2].keys())[row]
            rank_type = data_list[2][rank_type]

            key_en = f"{loc_en}({rank_type})"
            key_ru = f"{loc_ru}({rank_type})"
            remap_dict[key_ru] = key_en

    labels = [remap_dict.get(x, x) for x in labels]
    intervals = [0, 1, 20, 40, 60, 80, 100]

    fig = plt.figure(constrained_layout=True, figsize=(5, 2 + len(labels) * 0.5))
    fig.set_facecolor(facecolor)
    spec = gridspec.GridSpec(ncols=4, nrows=5, figure=fig)

    ax_image1 = fig.add_subplot(spec[0, 0])
    ax_image2 = fig.add_subplot(spec[0, -1])
    ax_title = fig.add_subplot(spec[0:1, 1:-1])
    ax_metrics = fig.add_subplot(spec[1:, 0:4])

    # Player image
    try:
        res1 = requests.get(player_pic, timeout=10)
        img1 = Image.open(io.BytesIO(res1.content))
        img_resized1 = img1.resize((100, int(img1.height * 100 / img1.width)))
        ax_image1.imshow(img_resized1)
    except Exception:
        pass
    ax_image1.axis('off')

    # Team image
    try:
        res2 = requests.get(team_pic, timeout=10)
        img2 = Image.open(io.BytesIO(res2.content))
        img_resized2 = img2.resize((100, int(img2.height * 100 / img2.width)))
        ax_image2.imshow(img_resized2)
    except Exception:
        pass
    ax_image2.axis('off')

    ax_title.text(0, 0.6, f"{player_name}", wrap=True, ha='left', va='center', color=linecolor, fontsize=18, fontweight='bold')
    ax_title.text(0, 0.4, f"\n{team_name}\nPosition: {player_position}", wrap=True, ha='left', va='center', color=linecolor, fontsize=10)
    ax_title.axis('off')

    y_pos = np.arange(len(values)) * 2
    bars_height = 0.6
    bars = ax_metrics.barh(y_pos, values, height=bars_height)

    colors = ['#8B0000', '#B22222', '#DAA520', '#9ACD32', '#006400']
    for i, val in enumerate(values):
        if val < 20:
            bars[i].set_color(colors[0])
        elif val < 40:
            bars[i].set_color(colors[1])
        elif val < 60:
            bars[i].set_color(colors[2])
        elif val < 80:
            bars[i].set_color(colors[3])
        else:
            bars[i].set_color(colors[4])

    ax_metrics.set_xticks(intervals)
    ax_metrics.spines['bottom'].set_edgecolor(linecolor)
    ax_metrics.spines['top'].set_edgecolor(linecolor)
    ax_metrics.spines['right'].set_edgecolor(linecolor)
    ax_metrics.spines['left'].set_edgecolor(linecolor)
    ax_metrics.tick_params(axis='y', colors=linecolor)
    ax_metrics.set_xbound(upper=111)
    ax_metrics.set_facecolor(bgcolor)

    for i in intervals:
        ax_metrics.axvline(i, color=ax_metrics.get_facecolor(), linewidth=5)

    for i in range(len(values)):
        ax_metrics.text(values[i] + 1, y_pos[i], f'{values[i]}%', va='center', color=linecolor)
        ax_metrics.text(6, y_pos[i] + bars_height * 1.1, labels[i], va='center', ha='left', color=linecolor, fontsize=12, fontweight='bold')

    ax_metrics.get_yaxis().set_ticks([])
    ax_metrics.get_xaxis().set_ticks([])
    ax_metrics.set_ylim([-1, y_pos.max() + 2])
    ax_metrics.set_title(f'{season_name}', color=linecolor)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_stat_histogram(user_data: dict, metric: str, locstr: dict) -> io.BytesIO | None:
    """Generates a distribution histogram comparing player against league peers."""
    client = get_wyscout_client()
    data = pd.DataFrame(user_data['data'])

    fig = plt.figure(figsize=(10, 6))
    counts, bins, bars = plt.hist(data[metric], color="dodgerblue", edgecolor="k")

    cmap = matplotlib.colormaps['coolwarm']
    norm = Normalize(vmin=counts.min(), vmax=counts.max())
    for c, b in zip(counts, bars):
        b.set_facecolor(cmap(norm(c)))

    matching_rows = data[data['player_id'] == user_data['wyscoutId']]
    if matching_rows.empty:
        print(f"Player {user_data['wyscoutId']} not found in dataset for histogram.")
        plt.close(fig)
        return None
    else:
        value_to_mark = matching_rows.iloc[0][metric]

    stat_df = fetch_metrics_csv()
    sdf = stat_df.transpose()
    sdf['nme'] = sdf.apply(lambda row: f"{row['label']}({row['rank_type']})", axis=1)
    mtype = sdf[sdf['nme'] == metric].iloc[0]['rank_type'] if 'nme' in sdf and not sdf[sdf['nme'] == metric].empty else "metric"

    plt.axvline(value_to_mark, color='red', linestyle='--')
    ymax = plt.ylim()[1]
    player_info = client.player(user_data['wyscoutId'])
    plt.annotate(
        f"{player_info['shortName']}\nP90:{round(value_to_mark, 2)}\n({round(user_data['percentiles'][metric])}({mtype}))",
        xy=(value_to_mark, 0.5),
        xytext=(value_to_mark + plt.xlim()[1] * 0.02, ymax),
        textcoords='data', va='top'
    )
    plt.ylim(0, ymax * 1.05)
    plt.title(f"{locstr.get('metric_dist', 'Distribution for')} {metric}")
    plt.xlabel(locstr.get('metric_dist_v', 'Value'))
    plt.ylabel(locstr.get('metric_dist_c', 'Count'))

    buf = io.BytesIO()
    plt.savefig(buf, format='jpg', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_performance_heatmap(user_data: dict) -> io.BytesIO | None:
    """Generates the personal performance heatmap table."""
    client = get_wyscout_client()
    data = pd.DataFrame(user_data['data'])
    matching_rows = data[data['player_id'] == user_data['wyscoutId']]
    if matching_rows.empty:
        print(f"Player {user_data['wyscoutId']} not found in dataset for heatmap.")
        return None
    else:
        data_row = matching_rows.iloc[0]

    pldata = data_row[list(user_data['percentiles'].keys())]
    z = pd.DataFrame([pldata, pd.Series(user_data['percentiles'])], index=['values(p90 if applicable)', 'percentiles'])
    z = round(z, 2)
    z = z[[i for i in z.columns if i not in ['player', 'team', 'player_id', 'mins']]]

    fig, ax = plt.subplots(figsize=(len(pldata) * 1.6, 4))
    sns.heatmap(z, annot=True, fmt=".2f", linewidths=.5, ax=ax, cmap='summer', cbar=False)
    player_info = client.player(user_data['wyscoutId'])
    plt.title(f"{player_info['shortName']} as {user_data['position']}:", fontsize=18)

    buf = io.BytesIO()
    plt.savefig(buf, format='jpg', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_position_pie(user_data: dict, pldocs: pd.DataFrame) -> io.BytesIO | None:
    """Generates a pie chart of positions played by minutes."""
    client = get_wyscout_client()

    def extract_pos(pos):
        for key, vals in POS_GROUPS.items():
            if pos in vals:
                return key
        return 'Unknown'

    pldocs['position'] = pldocs['player'].apply(lambda x: extract_pos(x['position']) if isinstance(x, dict) else 'Unknown')
    position_mins = pldocs.groupby('position')['mins'].sum()
    explode = [0] * len(position_mins)
    if len(explode) > 0:
        explode[0] = 0.1
    else:
        print("No positions found.")

    fig, ax = plt.subplots()
    ax.pie(position_mins, labels=position_mins.index, explode=explode, autopct='%1.1f%%', shadow=True, startangle=90)
    ax.axis('equal')
    player_info = client.player(user_data['wyscoutId'])
    plt.title(f"Positions: {player_info['shortName']}")

    buf = io.BytesIO()
    plt.savefig(buf, format='jpg', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf
