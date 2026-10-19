from datetime import date

from airport_system.db.connection import call_procedure, query


# Insert and updated stored procedure
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


# Delete flight stored procedure
def delete_flight(flight_id: int, force: bool=False):
    if flight_id is None:
        raise Exception("The flight ID cannot be null")

    args = {
        'p_flight_id': flight_id,
        'p_force': force
    }

    call_procedure('sp_delete_flight', args)


# Revenue report stored procedure
# noinspection SqlResolve
def revenue_report(date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    args = {
        'p_date_from': date_from,
        'p_date_to': date_to
    }

    return query("SELECT * FROM sp_revenue_report("
                 "p_date_from => %(p_date_from)s, p_date_to => %(p_date_to)s)", args)