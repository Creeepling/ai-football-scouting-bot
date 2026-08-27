import os
import json
import csv
from io import StringIO
import pandas as pd
from google.cloud import storage
from config import GCS_BUCKET_NAME

# In-memory cache for localization strings to avoid redundant disk reads
_loc_cache = {}


class GCSResponse:
    def __init__(self, data, ok):
        self._data = data
        self.status_code = 200 if ok else 404

    def json(self):
        return self._data


def get_gcs_bucket():
    client = storage.Client()
    return client.bucket(GCS_BUCKET_NAME)


def load_user_data(chat_id: int) -> GCSResponse:
    """Loads user session JSON from Google Cloud Storage."""
    bucket = get_gcs_bucket()
    blob = bucket.blob(f'{chat_id}.json')
    if not blob.exists():
        return GCSResponse(None, False)
    else:
        raw = blob.download_as_bytes()
        try:
            data = json.loads(raw)
            return GCSResponse(data, True)
        except Exception as e:
            print(f"Error parsing user data JSON for chat_id {chat_id}: {e}")
            return GCSResponse(None, False)


def save_user_data(chat_id: int, data) -> None:
    """Saves user session data (dict or JSON string) to Google Cloud Storage."""
    bucket = get_gcs_bucket()
    blob = bucket.blob(f'{chat_id}.json')
    if isinstance(data, dict):
        payload = json.dumps(data)
    else:
        payload = str(data)
    blob.upload_from_string(payload, content_type='application/json')


def get_or_init_user_info(chat_id: int) -> dict:
    """Retrieves user info dict or initializes with default language if not present."""
    response = load_user_data(chat_id)
    if response.status_code != 200:
        default_data = {'language': 'loc_en'}
        save_user_data(chat_id, default_data)
        return default_data
    else:
        data = response.json()
        if not data or 'language' not in data:
            data = data or {}
            data['language'] = 'loc_en'
            save_user_data(chat_id, data)
        return data


def update_language(chat_id: int, language: str) -> dict:
    """Updates user's preferred language code."""
    data = get_or_init_user_info(chat_id)
    data['language'] = language
    save_user_data(chat_id, data)
    return data


def load_localization(language_code: str = 'loc_en') -> dict:
    """Loads localization key-value mapping from JSON file."""
    if language_code in _loc_cache:
        return _loc_cache[language_code]
    else:
        file_path = os.path.join(os.path.dirname(__file__), f"{language_code}.json")
        if not os.path.exists(file_path):
            file_path = os.path.join(os.path.dirname(__file__), "loc_en.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loc_data = json.load(f)
                _loc_cache[language_code] = loc_data
                return loc_data
        except Exception as e:
            print(f"Error loading localization file {file_path}: {e}")
            return {}


def fetch_metrics_csv() -> pd.DataFrame | None:
    """Downloads metrics.csv from GCS and parses it into a DataFrame."""
    bucket = get_gcs_bucket()
    blob = bucket.blob('metrics.csv')
    if not blob.exists():
        print("Failed to download metrics.csv from GCS")
        return None
    else:
        csv_bytes = blob.download_as_bytes()
        data = StringIO(csv_bytes.decode('utf-8'))
        return pd.read_csv(data, index_col=0, encoding='utf-8')


def fetch_metrics_dicts() -> list[dict]:
    """Downloads metrics.csv from GCS and parses it into a list of row dicts."""
    bucket = get_gcs_bucket()
    blob = bucket.blob('metrics.csv')
    if not blob.exists():
        print("Failed to download metrics.csv from GCS")
        return []
    else:
        csv_bytes = blob.download_as_bytes()
        csv_text = csv_bytes.decode('utf-8')
        csv_lines = csv_text.strip().split("\n")
        csv_reader = csv.DictReader(csv_lines)
        return [row for row in csv_reader]
