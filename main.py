import functions_framework
from flask import Request

from config import ADMIN_TELEGRAM_ID, TELEGRAM_WEBHOOK_SECRET
from storage import (
    load_user_data,
    get_or_init_user_info,
    update_language,
    load_localization,
)
from telegram import (
    direct_message,
    send_menu,
    send_photo,
    delete_message,
    build_menu_buttons,
    notify_admin_error,
)
from charts import generate_player_card
from agent import run_scouting_agent


def get_user_id(body: dict) -> int:
    """Extracts chat / user ID from Telegram update payload."""
    if 'callback_query' in body:
        return body['callback_query']['message']['chat']['id']
    else:
        return body['message']['chat']['id']


def process_slashcommand(command: str, chat_id: int, locstr: dict, user_data: dict) -> None:
    """Handles Telegram slash commands."""
    if command == '/help':
        direct_message(chat_id, locstr.get('welcome', 'Welcome to Scouting Bot!'))
    elif command in ['/start', '/language']:
        labels = ['English', 'Русский']
        ids = ['loc_en', 'loc_ru']
        menu = build_menu_buttons(labels, ids)
        send_menu(chat_id, 'Choose your language / Выберите ваш язык', menu)
    elif command == '/card':
        buf = generate_player_card(user_data, locstr)
        if buf:
            send_photo(chat_id, buf, "card.png")
        else:
            direct_message(chat_id, locstr.get('card_no_analysis', "No analysis available."))
    elif command == '/seasons':
        direct_message(chat_id, locstr.get('season_list', 'Loading seasons...'))
        prompt = f"Request: Provide verbal career analysis for player wyscout_id *{user_data.get('wyscoutId')}*."
        run_scouting_agent(prompt, chat_id)
    elif command == '/performance':
        prompt = "Request:***Show me this player's personal performance.*** You have the id, performance, season and position data*."
        run_scouting_agent(prompt, chat_id)
    elif command == '/positions':
        prompt = "Request:***Show me the positions the player played in.*** You have the id, performance, season and position data*."
        run_scouting_agent(prompt, chat_id)
    elif command == '/current':
        prompt = "Look up currently stored player data."
        run_scouting_agent(prompt, chat_id)
    elif command == '/metric':
        if 'data' in user_data:
            labels = [k for k in user_data['data'].keys() if k not in ['player', 'team', 'player_id', 'mins', '90s']]
            ids = ['m' + k for k in labels]
            menu = build_menu_buttons(labels, ids)
            send_menu(chat_id, locstr.get('select_a_metric', 'Select a metric:'), menu)
        else:
            direct_message(chat_id, locstr.get('no_data_stored', "No data stored."))
    else:
        run_scouting_agent(command, chat_id)


def process_button(body: dict, chat_id: int, locstr: dict, user_data: dict) -> None:
    """Handles Telegram inline keyboard callback queries."""
    callback_data = body['callback_query']['data']
    keyboard = body['callback_query']['message']['reply_markup']['inline_keyboard']
    choice = next((btn['text'] for row in keyboard for btn in row if btn['callback_data'] == callback_data), '')

    direct_message(chat_id, f"{locstr.get('processing', 'Processing')}: {choice}.")

    if callback_data.startswith('s'):
        prompt = f"Request: You currently have career data for a player. Show season data for them for season_id:{callback_data[1:]}."
        run_scouting_agent(prompt, chat_id)
    elif callback_data.startswith('m'):
        prompt = f"Request: Plot me his metric for {callback_data[1:]}. You have the id, performance, season and position data."
        run_scouting_agent(prompt, chat_id)
    elif callback_data.startswith('loc_'):
        update_language(chat_id, callback_data)
        new_loc = load_localization(callback_data)
        direct_message(chat_id, new_loc.get('welcome', 'Welcome!'))


def repeated_request(user_data: dict, message: str, chat_id: int) -> None:
    """Dispatches freeform follow-up questions to the LangChain agent."""
    prompt = (
        f"Request:***{message}***. You currently have career data for player id "
        f"*{user_data.get('wyscoutId')}* for season id *{user_data.get('season')}*, "
        f"for position *{user_data.get('position')}*."
    )
    run_scouting_agent(prompt, chat_id)


def process_link(url: str, chat_id: int) -> None:
    """Dispatches a Transfermarkt link to the LangChain agent."""
    prompt = f"Here's a link: {url}. What is this player's career data?"
    run_scouting_agent(prompt, chat_id)


@functions_framework.http
def handler(request: Request):
    """Google Cloud Functions HTTP entry point."""
    try:
        if TELEGRAM_WEBHOOK_SECRET:
            token_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if token_header != TELEGRAM_WEBHOOK_SECRET:
                return {'statusCode': 403, 'body': 'Forbidden: Invalid secret token'}
        else:
            pass

        body = request.get_json(silent=True)
        if not body:
            return {'statusCode': 400, 'body': 'No JSON payload'}

        dialogue_id = get_user_id(body)
        user_info = get_or_init_user_info(dialogue_id)
        lang = user_info.get('language', 'loc_en')
        locstr = load_localization(lang)

        if 'callback_query' in body:
            cb_msg = body['callback_query']['message']
            delete_message(cb_msg['chat']['id'], cb_msg['message_id'])
            process_button(body, dialogue_id, locstr, user_info)
            return {'statusCode': 200}

        message_text = body.get('message', {}).get('text', '')

        if 'transfermarkt' in message_text:
            direct_message(ADMIN_TELEGRAM_ID, message_text)
            direct_message(dialogue_id, locstr.get('link_accepted', 'Link accepted, analyzing...'))
            process_link(message_text, dialogue_id)
            return {'statusCode': 200}

        if message_text.startswith('/'):
            process_slashcommand(message_text, dialogue_id, locstr, user_info)
            return {'statusCode': 200}

        stored_resp = load_user_data(dialogue_id)
        if stored_resp.status_code != 200:
            direct_message(dialogue_id, locstr.get('provide_link', 'Please provide a Transfermarkt link.'))
        else:
            repeated_request(stored_resp.json(), message_text, dialogue_id)

        return {'statusCode': 200}

    except Exception as ex:
        print(f"Error handling request: {ex}")
        notify_admin_error(ex)
        return {'statusCode': 200}
