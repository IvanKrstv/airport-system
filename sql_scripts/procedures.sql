CREATE OR REPLACE PROCEDURE sp_insert_update_passenger(
    p_passenger_id INTEGER,
    p_passport_id VARCHAR,
    p_passenger_name VARCHAR,
    p_country_name VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_country_id INTEGER := null;
BEGIN
    IF p_passport_id IS NULL OR trim(p_passport_id) = '' THEN
        RAISE EXCEPTION 'Passport ID cannot be null or empty';
    end if;

    IF EXISTS(
    SELECT 1 FROM Passenger
    WHERE passport_id = p_passport_id
      AND (p_passenger_id IS NULL OR passenger_id <> p_passenger_id)
    ) THEN
        RAISE EXCEPTION 'Passport ID % already exists. Cannot be duplicated', p_passport_id;
    end if;

    IF p_passenger_name IS NULL OR trim(p_passenger_name) = '' THEN
        RAISE EXCEPTION 'Passenger name cannot be null or empty';
    end if;

    IF p_country_name IS NULL OR trim(p_country_name) = '' THEN
        RAISE EXCEPTION 'Country cannot be null or empty';
    end if;

    v_country_id = (SELECT country_id from country where p_country_name ILIKE country_name);
    IF v_country_id IS NULL THEN
        RAISE EXCEPTION 'There is no such country in the record.';
    end if;

    IF p_passenger_id IS NULL THEN
        INSERT INTO passenger (passport_id, passenger_name, country_id)
        VALUES (p_passport_id, p_passenger_name, v_country_id);
    ELSIF NOT EXISTS(
        SELECT 1 from passenger where passenger_id = p_passenger_id
    ) THEN
        RAISE EXCEPTION 'Passenger with ID % not found', p_passenger_id;
    ELSE
        UPDATE passenger
        SET passport_id = p_passport_id, passenger_name = p_passenger_name, country_id = v_country_id
        WHERE passenger_id = p_passenger_id;
    end if;

end;
$$;


--------------------------------------------------------


CREATE OR REPLACE PROCEDURE sp_delete_flight(
    p_flight_id INTEGER,
    p_force BOOLEAN DEFAULT FALSE
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM Flight WHERE flight_id = p_flight_id) THEN
        RAISE EXCEPTION 'Flight with ID % not found', p_flight_id;
    END IF;

    IF p_force THEN
        DELETE FROM Ticket WHERE flight_id = p_flight_id;
    ELSIF EXISTS (SELECT 1 FROM Ticket WHERE flight_id = p_flight_id) THEN
        RAISE EXCEPTION 'Cannot delete flight % - has tickets. Use p_force=TRUE to delete anyway.', p_flight_id;
    END IF;

    DELETE FROM Flight WHERE flight_id = p_flight_id;
END;
$$;


--------------------------------------------------------


-- function because it returns a table
CREATE OR REPLACE FUNCTION sp_revenue_report(
    p_date_from DATE DEFAULT NULL,
    p_date_to DATE DEFAULT NULL
)
RETURNS TABLE (
    from_city VARCHAR,
    to_city VARCHAR,
    seat_class VARCHAR,
    tickets_sold BIGINT,
    total_revenue NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d_from.city_name as from_city,
        d_to.city_name AS to_city,
        sc.seat_class_name AS seat_class,
        COUNT(t.ticket_id) AS tickets_sold,
        SUM(t.final_price) AS total_revenue
    FROM Ticket t
    JOIN Flight f ON f.flight_id = t.flight_id
    JOIN Plane p ON p.plane_id = f.plane_id
    JOIN Destination d_from ON d_from.destination_id = f.from_destination_id
    JOIN Destination d_to ON d_to.destination_id = f.to_destination_id
    JOIN Seat s ON s.seat_id = t.seat_id
    JOIN SeatClass sc ON sc.seat_class_id = s.seat_class_id
    WHERE (p_date_from IS NULL OR t.sold_at::date >= p_date_from)
      AND (p_date_to IS NULL OR t.sold_at::date <= p_date_to)
    GROUP BY d_from.destination_id, d_to.destination_id, sc.seat_class_id, d_from.city_name, d_to.city_name, sc.seat_class_name
    ORDER BY total_revenue DESC;
END;
$$;