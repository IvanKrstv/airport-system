from datetime import date

from airport_system.db.connection import call_procedure, query, get_connection


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
def delete_flight(flight_id: int, force: bool = False) -> None:
    if flight_id is None:
        raise ValueError("The flight ID cannot be null")

    args = {
        'p_flight_id': flight_id,
        'p_force': force
    }

    call_procedure('sp_delete_flight', args)


# Revenue report function
# noinspection SqlResolve
def revenue_report(date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    args = {
        'p_date_from': date_from,
        'p_date_to': date_to
    }

    return query("SELECT * FROM sp_revenue_report("
                 "p_date_from => %(p_date_from)s, p_date_to => %(p_date_to)s)", args)


# Revenue report cursor
def revenue_report_cursor(date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    with get_connection() as connection:
        connection.execute(
            "CALL sp_revenue_report_cursor(%(d1)s, %(d2)s, 'revenue_cursor')",
            {'d1': date_from, 'd2': date_to}
        )
        return connection.execute("FETCH ALL FROM revenue_cursor").fetchall()


# Sell ticket stored procedure
def sell_ticket(flight_id: int, seat_name: str, passport_id: str,
                passenger_name: str | None, country_name: str | None,
                employee_id: int) -> None:
    if flight_id is None:
        raise ValueError("The flight ID cannot be null")

    args = {
        'p_flight_id': flight_id,
        'p_seat_name': seat_name,
        'p_passport_id': passport_id,
        'p_passenger_name': passenger_name,
        'p_country_name': country_name,
        'p_employee_id': employee_id
    }

    call_procedure('sell_ticket', args, autocommit=True)


# Flight stats stored procedure
def flight_stats(flight_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "CALL sp_flight_stats(%s, NULL, NULL, NULL)", [flight_id]
        ).fetchone()
        return {
            'tickets_sold': row['p_tickets_sold'],
            'revenue': row['p_revenue'],
            'free_seats': row['p_free_seats'],
        }