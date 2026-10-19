from airport_system.db.connection import call_procedure


def insert_update_passenger(passenger_id: int | None, passport_id: str,
                            passenger_name: str, country_name: str) -> None:
    args = {
        'p_passenger_id': passenger_id,
        'p_passport_id': passport_id,
        'p_passenger_name': passenger_name,
        'p_country_name': country_name
    }

    call_procedure('sp_insert_update_passenger', args)


def add_passenger(passport_id: str, passenger_name: str, country_name: str) -> None:
    insert_update_passenger(None, passport_id, passenger_name, country_name)


def update_passenger(passenger_id: int, passport_id: str, passenger_name: str, country_name: str) -> None:
    insert_update_passenger(passenger_id, passport_id, passenger_name, country_name)