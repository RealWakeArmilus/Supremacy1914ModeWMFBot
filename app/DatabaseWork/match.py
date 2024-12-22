from asyncio.log import logger
import sqlite3
from SPyderSQL import SQLite


async def extraction_names_states(type_map_match: str) -> list:

    if type_map_match == 'Великая война':

        return ["Финляндия", "Австро-венгрия", "Аравия", "Великобритания", "Восточная ливия",
                "Восточный алжир", "Германская империя", "Гренландия", "Греция", "Египет",
                "Западная ливия", "Западный алжир", "Испания", "Италия", "Кавказ",
                "Литва", "Марокко", "Норвегия", "Османская империя", "Польша",
                "Россия", "Румыния", "Северная канада", "Северная россия", "Северные США",
                "Франция", "Центральные США", "Швеция", "Южная канада", "Южные США"]


async def get_free_states_from_match_for_user(number_match_db: str) -> list:
    """
    :param number_match_db: 'database/{number_match_db}.db'
    :return: actual list free states from match for user
    """
    data_number_match = SQLite.select_table(f'database/{number_match_db}.db',
                                            'states',
                                            ['name', 'telegram_id'])

    states_from_match = list()

    for data_state in data_number_match:
        if data_state['telegram_id'] == 0:
            states_from_match.append(data_state['name'])

    return states_from_match


async def check_request_choice_state(number_match_db: str, user_id: int) -> bool:
    """
    Is there a player's application in the database?
    \nЕсть ли заявка от игрока в базе данных?

    :param number_match_db: 'database/{number_match_db}.db'
    :param user_id: message.from_user.id
    :return: True - заявка еще ждет проверки, False - заявка нет.
    """
    data_requests = SQLite.select_table(f'database/{number_match_db}.db',
                                           'request_choice_state',
                                           ['telegram_id'])

    for request in data_requests:
        if request['telegram_id'] == user_id:
            return True

    return False


async def check_choice_state_in_match_db(number_match_db: str, user_id: int) -> dict | None:
    """
    checking the user in the list of countries. Perhaps his application has already been checked and approved.
    \nПроверка пользователя в списке государств. возможно его заявка уже прошла проверку и ее одобрили.
    \n\nIs the player already assigned to a specific country?
    \nИгрок уже закреплен за конкретным государством?

    :param number_match_db: 'database/{number_match_db}.db'
    :param user_id: message.from_user.id
    :return: dict - заявка прошла проверку и ее одобрили, None - заявка прошла проверку и ее отклонили.
    """
    data_state = SQLite.select_table(f'database/{number_match_db}.db',
                                           'states',
                                           ['name', 'telegram_id'])

    for state in data_state:
        if state['telegram_id'] == user_id:
            return {'telegram_id': state['telegram_id'], 'name_state': state['name']}

    return None


async def save_request_choice_state(user_id: int, number_match: str, name_state: str, unique_word: str, admin_decision_message_id: int):
    """
    Сохраняет заявку пользователя на выбор государства в базу данных.

    :param admin_decision_message_id:
    :param user_id: Telegram ID пользователя callback.from_user.id
    :param number_match: Номер матча
    :param name_state: Название выбранного государства
    :param unique_word: Кодовое слово
    """
    try:
        # Check for None
        if user_id is None or number_match is None or name_state is None or unique_word is None or admin_decision_message_id is None:
            raise ValueError("One or more parameters are missing! Missing required parameters.")

        # Checking Type Conformance
        assert isinstance(user_id, int), "user_id должен быть целым числом"
        assert isinstance(number_match, str) and number_match.isdigit(), "number_match должен быть числом в виде строки"
        assert isinstance(name_state, str), "name_state должен быть строкой"
        assert isinstance(unique_word, str), "unique_word должен быть строкой"
        assert isinstance(admin_decision_message_id, int), "admin_decision_message_id должен быть int"

        # Preparing data for insertion
        column_names = ['telegram_id', 'number_match', 'name_state', 'unique_word', 'admin_decision_message_id']
        values = (user_id, int(number_match), name_state, unique_word, admin_decision_message_id)

        # Checking data length
        if len(column_names) != len(values):
            raise ValueError(f"Mismatch between columns and values! Values: {values} for Columns: {column_names}")

        # Inserting data into the database
        SQLite.insert_table(f'database/{number_match}.db',
                            'request_choice_state',
                            column_names,
                            values
        )
    except ValueError as error:
        print(f'Error "app/DatabaseWork/match/save_request_choice_state": {error}')


async def get_data_user_for_request(unique_word: str, number_match: str) -> dict:
    """
    Возвращает все базовые данные заявки определённого матча, на регистрацию пользователя конкретного государства

    :param unique_word: кодовое слово
    :param number_match: номер матча
    :return: данные заявки {'telegram_id': user['telegram_id'], 'name_state': user['name_state'], 'number_match': number_match}
    """

    data_users = SQLite.select_table(f'database/{number_match}.db',
                                    'request_choice_state',
                                    ['telegram_id', 'name_state', 'unique_word', 'admin_decision_message_id'])

    for user in data_users:
        if user['unique_word'] == unique_word:
            return {'telegram_id': user['telegram_id'], 'name_state': user['name_state'], 'number_match': number_match, 'unique_word': user['unique_word'], 'admin_decision_message_id': user['admin_decision_message_id']}


async def deleted_request_state_in_match(data_user: dict):
    """
    Удаляет заявку на подтверждения государства в конкретном матче

    :param data_user:
    :return:
    """
    try:
        with sqlite3.connect(f'database/{data_user['number_match']}.db') as db:
            db.execute("DELETE FROM request_choice_state WHERE unique_word = ?", (data_user['unique_word'],))
            db.commit()
            return True
    except sqlite3.Error as e:
        print(f"Ошибка при удалении заявки на подтверждения государства: {data_user['name_state']}: {e}")
        return False


async def register_state_in_match(data_user: dict):
    """
    Регистрирует пользователя в конкретном матче на конкретное государство. Совершать только после подтверждения админа.

    :param data_user: {'telegram_id': user['telegram_id'], 'name_state': user['name_state'], 'number_match': number_match}
    """
    # change telegram id of the appropriate state
    SQLite.update_table(f'database/{data_user['number_match']}.db',
                        'states',
                        {'telegram_id': data_user['telegram_id']},
                        {'name': data_user['name_state']})

    await deleted_request_state_in_match(data_user)

