import numpy as np
import pandas as pd


def get_position_metrics(pos: str, df: pd.DataFrame) -> pd.DataFrame:
    """Filters metrics relevant to a specific player role."""
    sdf = df.transpose()
    out = []
    if pos == 'goalkeeper':
        out.append('goalkeeper')
    if pos == 'winger':
        out.append('creator')
        out.append('wide')
    if pos == "attacking midfielder / second striker":
        out.append('creator')
        out.append('attacking_midfielder')
    if pos == "central midfielder":
        out.append('ball_winner')
        out.append('passer')
    if pos == 'central defender':
        out.append('ball_winner')
        out.append('passer')
    if pos == 'full back':
        out.append('ball_winner')
        out.append('defence')
    if pos == 'striker':
        out.append('finisher')
        out.append('forward')
    return pd.concat([sdf[sdf['role'].apply(lambda x: any(f in str(x) for f in out))]])


def calculate_beta_raw(df: pd.DataFrame, metric: pd.Series, ranked_df: pd.DataFrame, language: str = 'loc_en') -> None:
    """Calculates Bayesian weighted average for beta ranked metrics."""
    m = df[metric['att_colname']].quantile(0.80)
    c_mean = df[metric['colname']].mean()
    v = df[metric['att_colname']]
    r = df[metric['colname']]
    bayes_rank = (r * v + c_mean * m) / (v + m)
    col_name = f"{metric[language]}({metric['rank_type']})"
    ranked_df[col_name] = bayes_rank


def calculate_raws(trtots: pd.DataFrame, stat_df: pd.DataFrame, p_absolute: pd.DataFrame, language: str = 'loc_en') -> pd.DataFrame:
    """Calculates raw / per90 values for each metric."""
    ranked_df = p_absolute[['player', 'team', 'player_id', 'mins', '90s']].copy()
    for stat in trtots.iloc:
        metric = stat_df[stat['colname']]
        rank_type = metric["rank_type"]
        col_name = f"{metric[language]}({rank_type})"

        if rank_type == "percentile":
            skip_p90_val = str(metric.get("skip_p90", "")).strip().lower()
            skip_p90 = skip_p90_val not in ['empty', 'nan', 'false', '0', '', 'none']
            if skip_p90:
                ranked_df[col_name] = p_absolute[metric['colname']]
            else:
                ranked_df[col_name] = p_absolute[metric['colname']] / p_absolute['90s']
        elif rank_type == "percentage":
            ranked_df[col_name] = np.where(
                p_absolute[metric['att_colname']] == 0,
                0,
                p_absolute[metric['colname']] / p_absolute[metric['att_colname']]
            )
        elif rank_type == "beta":
            calculate_beta_raw(p_absolute, metric, ranked_df, language)
        elif rank_type == "average":
            ranked_df[col_name] = p_absolute[metric['colname']] / p_absolute[metric['att_colname']]
        else:
            raise ValueError(f"Unsupported rank_type '{rank_type}'")
    return ranked_df


def calculate_ranks(trtots: pd.DataFrame, stat_df: pd.DataFrame, p_raws: pd.DataFrame, language: str = 'loc_en') -> pd.DataFrame:
    """Converts raw metrics into percentile rank values (0-100)."""
    ranked_df = p_raws[['player', 'team', 'player_id', 'mins']].copy()
    for stat in trtots.iloc:
        metric = stat_df[stat['colname']]
        asc_val = str(metric.get('ascending', '')).strip().lower()
        if asc_val in ['false', '0']:
            ascending = False
        else:
            ascending = True
        name = f"{metric[language]}({metric['rank_type']})"
        ranked_df[name] = np.rint((p_raws[name]).rank(method='max', pct=True, ascending=ascending) * 100).astype(int)
    return ranked_df
