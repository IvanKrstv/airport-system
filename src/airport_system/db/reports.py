from airport_system.db.connection import query
from airport_system.db import queries


# Helper functions
def _none_if_empty(value: str | None):
    """
    Helper function to prevent an empty string from reaching the query
    :param value: str or None
    :return: value or None
    """
    return value.strip() or None if isinstance(value, str) else value

def _check_period(date_from, date_to):
    """
    Helper function to prevent the start date to exceed the end date
    """
    if date_from is None or date_to is None:
        return

    if date_from and date_to and date_from > date_to:
        raise ValueError("The start date cannot be after the end date.")



# Query wrappers
def search_flights(from_city=None, to_city=None, date_from=None, date_to=None, company=None) -> list[dict]:
    _check_period(date_from, date_to)

    return query(queries.SEARCH_FLIGHTS_QUERY, {
        'from_city': _none_if_empty(from_city), 'to_city': _none_if_empty(to_city),
        'date_from': date_from, 'date_to': date_to,
        'company': _none_if_empty(company)
    })


def passengers_per_flight(flight_id: int) -> list[dict]:
    return query(queries.PASSENGERS_PER_FLIGHT_QUERY, {'flight_id': flight_id})


def occupancy_per_flight(date_from=None, date_to=None) -> list[dict]:
    _check_period(date_from, date_to)

    return query(queries.OCCUPANCY_QUERY, {
        'date_from': date_from, 'date_to': date_to
    })


def revenue_per_seat_class(date_from=None, date_to=None) -> list[dict]:
    _check_period(date_from, date_to)

    return query(queries.REVENUE_BY_CLASS_QUERY, {
        'date_from': date_from, 'date_to': date_to
    })


def top_destinations(top_n: int, date_from=None, date_to=None) -> list[dict]:
    if top_n < 1:
        raise ValueError("Number of destinations must be at least 1.")

    _check_period(date_from, date_to)

    return query(queries.TOP_DESTINATIONS_QUERY, {
        'top_n': top_n, 'date_from': date_from, 'date_to': date_to
    })


def frequent_travelers(months_ago: int, min_trips: int) -> list[dict]:
    if months_ago < 1:
        raise ValueError("The period cannot be less than 1 month.")
    if min_trips < 1:
        raise ValueError("The minimum trips cannot be less than 1.")

    return query(queries.FREQUENT_TRAVELERS_QUERY, {
        'months': months_ago, 'min_trips': min_trips
    })


def budget_flights(from_city=None, to_city=None, date_from=None, date_to=None) -> list[dict]:
    _check_period(date_from, date_to)

    return query(queries.BUDGET_FLIGHTS_QUERY, {
        'from_city': _none_if_empty(from_city), 'to_city': _none_if_empty(to_city),
        'date_from': date_from, 'date_to': date_to
    })


def no_flight_planes(date_from=None, date_to=None, company=None) -> list[dict]:
    _check_period(date_from, date_to)

    return query(queries.NO_FLIGHT_PLANES_QUERY, {
        'date_from': date_from, 'date_to': date_to, 'company': _none_if_empty(company)
    })


# Test
print(passengers_per_flight(4))