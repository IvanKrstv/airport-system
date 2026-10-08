# Search flights by destination, date and company
# noinspection SqlResolve
SEARCH_FLIGHTS_QUERY = """
SELECT
    f.flight_timestamp::date,
    d_from.city_name AS from_city,
    d_to.city_name   AS to_city,
    f.price,
    m.model_name,
    c.company_name
FROM Flight f
JOIN Destination d_from ON d_from.destination_id = f.from_destination_id
JOIN Destination d_to   ON d_to.destination_id   = f.to_destination_id
JOIN Plane p            ON p.plane_id = f.plane_id
JOIN Model m            ON m.model_id = p.model_id
JOIN Company c          ON c.company_id = m.company_id
WHERE (%(from_city)s::text IS NULL OR d_from.city_name ILIKE %(from_city)s::text)
  AND (%(to_city)s::text   IS NULL OR d_to.city_name   ILIKE %(to_city)s::text)
  AND (%(date_from)s::date IS NULL OR f.flight_timestamp::date >= %(date_from)s::date)
  AND (%(date_to)s::date   IS NULL OR f.flight_timestamp::date <= %(date_to)s::date)
  AND (%(company)s::text   IS NULL OR c.company_name ILIKE %(company)s::text)
ORDER BY f.flight_timestamp;
"""


# Information for the passengers per flight
# noinspection SqlResolve
PASSENGERS_PER_FLIGHT_QUERY = """
SELECT
    p.passport_id,
    p.passenger_name,
    s.seat_name        AS seat,
    sc.seat_class_name AS seat_class
FROM Ticket t
JOIN Passenger p  ON p.passenger_id = t.passenger_id
JOIN Seat s       ON s.seat_id = t.seat_id
JOIN SeatClass sc ON sc.seat_class_id = s.seat_class_id
WHERE t.flight_id = %(flight_id)s
ORDER BY p.passport_id;
"""


# Occupancy of each flight
# noinspection SqlResolve
OCCUPANCY_QUERY = """
SELECT
    f.flight_timestamp,
    d_from.city_name   AS from_city,
    d_to.city_name     AS to_city,
    m.model_name,
    c.company_name,
    COUNT(t.ticket_id) AS seats_occupied,
    m.model_capacity
FROM Flight f
JOIN Destination d_from ON d_from.destination_id = f.from_destination_id
JOIN Destination d_to   ON d_to.destination_id   = f.to_destination_id
JOIN Plane p            ON p.plane_id = f.plane_id
JOIN Model m            ON m.model_id = p.model_id
JOIN Company c          ON c.company_id = m.company_id
LEFT JOIN Ticket t      ON t.flight_id = f.flight_id
WHERE (%(date_from)s::date IS NULL OR f.flight_timestamp::date >= %(date_from)s::date)
  AND (%(date_to)s::date   IS NULL OR f.flight_timestamp::date <= %(date_to)s::date)
GROUP BY f.flight_id, f.flight_timestamp,
         d_from.city_name, d_to.city_name,
         m.model_name, m.model_capacity, c.company_name
ORDER BY f.flight_timestamp;
"""


# Total revenue per seat class in a period
# noinspection SqlResolve
REVENUE_BY_CLASS_QUERY = """
SELECT
    sc.seat_class_name AS seat_class,
    COUNT(t.ticket_id) AS tickets_sold,
    SUM(t.final_price) AS revenue
FROM Ticket t
JOIN Seat s       ON s.seat_id = t.seat_id
JOIN SeatClass sc ON sc.seat_class_id = s.seat_class_id
WHERE (%(date_from)s::date IS NULL OR t.sold_at::date >= %(date_from)s::date)
  AND (%(date_to)s::date   IS NULL OR t.sold_at::date <= %(date_to)s::date)
GROUP BY sc.seat_class_id, sc.seat_class_name
ORDER BY revenue DESC;
"""


# Most profitable destinations for a period (by sale date)
# noinspection SqlResolve
TOP_DESTINATIONS_QUERY = """
SELECT
    d.city_name,
    COUNT(t.ticket_id) AS total_tickets,
    SUM(t.final_price) AS total_revenue
FROM Ticket t
JOIN Flight f      ON f.flight_id = t.flight_id
JOIN Destination d ON d.destination_id = f.to_destination_id
WHERE (%(date_from)s::date IS NULL OR t.sold_at::date >= %(date_from)s::date)
  AND (%(date_to)s::date   IS NULL OR t.sold_at::date <= %(date_to)s::date)
GROUP BY d.destination_id, d.city_name
ORDER BY total_revenue DESC, total_tickets DESC
LIMIT %(top_n)s;
"""


# Frequent travelers in a period
# noinspection SqlResolve
FREQUENT_TRAVELERS_QUERY = """
SELECT
    p.passenger_name,
    c.country_name     AS nationality,
    COUNT(t.ticket_id) AS total_trips
FROM Ticket t
JOIN Flight f    ON f.flight_id = t.flight_id
JOIN Passenger p ON p.passenger_id = t.passenger_id
JOIN Country c   ON c.country_id = p.country_id
WHERE f.flight_timestamp::date >= current_date - make_interval(months => %(months)s::int)
  AND f.flight_timestamp::date <= current_date
GROUP BY p.passenger_id, p.passenger_name, c.country_id, c.country_name
HAVING COUNT(t.ticket_id) >= %(min_trips)s
ORDER BY total_trips DESC, p.passenger_name;
"""


