CREATE OR REPLACE PROCEDURE sp_insert_update_passenger(
    p_passenger_id passenger.passenger_id%type,
    p_passport_id passenger.passport_id%type,
    p_passenger_name passenger.passenger_name%type,
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
    WHERE passport_id = trim(p_passport_id)
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

    v_country_id = (SELECT country_id from country where lower(trim(p_country_name)) = lower(country_name));
    IF v_country_id IS NULL THEN
        RAISE EXCEPTION 'There is no such country in the record.';
    end if;

    IF p_passenger_id IS NULL THEN
        INSERT INTO passenger (passport_id, passenger_name, country_id)
        VALUES (trim(p_passport_id), trim(p_passenger_name), v_country_id);
    ELSIF NOT EXISTS(
        SELECT 1 from passenger where passenger_id = p_passenger_id
    ) THEN
        RAISE EXCEPTION 'Passenger with ID % not found', p_passenger_id;
    ELSE
        UPDATE passenger
        SET passport_id = trim(p_passport_id), passenger_name = trim(p_passenger_name), country_id = v_country_id
        WHERE passenger_id = p_passenger_id;
    end if;

end;
$$;


--------------------------------------------------------


CREATE OR REPLACE PROCEDURE sp_delete_flight(
    p_flight_id flight.flight_id%type,
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
    JOIN Destination d_from ON d_from.destination_id = f.from_destination_id
    JOIN Destination d_to ON d_to.destination_id = f.to_destination_id
    JOIN Seat s ON s.seat_id = t.seat_id
    JOIN SeatClass sc ON sc.seat_class_id = s.seat_class_id
    WHERE (p_date_from IS NULL OR t.sold_at::date >= p_date_from)
      AND (p_date_to IS NULL OR t.sold_at::date <= p_date_to)
    GROUP BY d_from.destination_id, d_to.destination_id, sc.seat_class_id, d_from.city_name, d_to.city_name, sc.seat_class_name
    ORDER BY total_revenue DESC, from_city, to_city, seat_class;
END;
$$;


--------------------------------------------------------


-- returns a cursor for the task
CREATE OR REPLACE PROCEDURE sp_revenue_report_cursor(
    p_date_from DATE DEFAULT NULL,
    p_date_to DATE DEFAULT NULL,
    INOUT p_cursor refcursor DEFAULT 'revenue_cursor'
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_date_from IS NOT NULL AND p_date_to IS NOT NULL AND p_date_from > p_date_to THEN
        RAISE EXCEPTION 'The start date cannot be after the end date.';
    END IF;

    OPEN p_cursor FOR
        SELECT
            d_from.city_name as from_city,
            d_to.city_name AS to_city,
            sc.seat_class_name AS seat_class,
            COUNT(t.ticket_id) AS tickets_sold,
            SUM(t.final_price) AS total_revenue
        FROM Ticket t
        JOIN Flight f ON f.flight_id = t.flight_id
        JOIN Destination d_from ON d_from.destination_id = f.from_destination_id
        JOIN Destination d_to ON d_to.destination_id = f.to_destination_id
        JOIN Seat s ON s.seat_id = t.seat_id
        JOIN SeatClass sc ON sc.seat_class_id = s.seat_class_id
        WHERE (p_date_from IS NULL OR t.sold_at::date >= p_date_from)
          AND (p_date_to IS NULL OR t.sold_at::date <= p_date_to)
        GROUP BY d_from.destination_id, d_to.destination_id, sc.seat_class_id, d_from.city_name, d_to.city_name, sc.seat_class_name
        ORDER BY total_revenue DESC, from_city, to_city, seat_class;
END;
$$;


--------------------------------------------------------


CREATE OR REPLACE PROCEDURE sell_ticket(
    p_flight_id flight.flight_id%type,
    p_seat_name seat.seat_name%type,
    p_passport_id passenger.passport_id%type,
    p_passenger_name passenger.passenger_name%type,
    p_country_name country.country_name%type,
    p_employee_id employee.employee_id%type
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_seat_id INTEGER;
    v_passenger_id INTEGER ;
    v_country_id INTEGER;
    v_flight_price NUMERIC;
    v_seat_class_increase_percentage INTEGER;
    v_final_price NUMERIC(10,2);
    v_error TEXT;
BEGIN
    BEGIN
        p_seat_name := trim(p_seat_name);
        p_passport_id := trim(p_passport_id);

        IF p_seat_name IS NULL OR p_seat_name = '' THEN
            RAISE EXCEPTION 'A seat is not assigned and is required';
        end if;

        IF p_passport_id IS NULL OR p_passport_id = '' THEN
            RAISE EXCEPTION 'A passport ID is not assigned and is required';
        end if;

        SELECT price INTO v_flight_price FROM flight WHERE (p_flight_id = flight_id);
        IF v_flight_price IS NULL THEN
            RAISE EXCEPTION 'Flight % not found', p_flight_id;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM Employee WHERE employee_id = p_employee_id) THEN
            RAISE EXCEPTION 'Employee % not found', p_employee_id;
        END IF;


        SELECT s.seat_id, sc.percent_increase INTO v_seat_id, v_seat_class_increase_percentage
        FROM Flight f
        JOIN Seat s ON s.plane_id = f.plane_id
        JOIN SeatClass sc ON sc.seat_class_id = s.seat_class_id
        WHERE f.flight_id = p_flight_id
               AND s.seat_name = p_seat_name;
        IF v_seat_id IS NULL THEN
            RAISE EXCEPTION 'Seat % does not exist on the plane of flight %', p_seat_name, p_flight_id;
        END IF;


        SELECT passenger_id INTO v_passenger_id
        FROM Passenger WHERE passport_id = p_passport_id;

        IF v_passenger_id IS NULL THEN
            IF p_passenger_name IS NULL OR trim(p_passenger_name) = '' THEN
                RAISE EXCEPTION 'A name is required for a new passenger';
            END IF;

            SELECT country_id INTO v_country_id
            FROM Country WHERE lower(country_name) = lower(trim(p_country_name));
            IF v_country_id IS NULL THEN
                RAISE EXCEPTION 'There is no such country in the record.';
            END IF;

            INSERT INTO Passenger (passport_id, passenger_name, country_id)
            VALUES (p_passport_id, trim(p_passenger_name), v_country_id)
            RETURNING passenger_id INTO v_passenger_id;
        END IF;

        IF EXISTS (SELECT 1 FROM Ticket WHERE flight_id = p_flight_id AND seat_id = v_seat_id) THEN
            RAISE EXCEPTION 'Seat % is already taken on flight %', p_seat_name, p_flight_id;
        END IF;

        v_final_price := round((v_flight_price + (v_seat_class_increase_percentage / 100.0) * v_flight_price), 2);

        INSERT INTO TICKET (seat_id, flight_id, passenger_id, employee_id, final_price)
        VALUES (v_seat_id, p_flight_id, v_passenger_id, p_employee_id, v_final_price);

    EXCEPTION WHEN OTHERS THEN
        v_error := SQLERRM; -- вградена променлива с текста на грешката
    END;

    if v_error IS NULL THEN
        COMMIT;
    ELSE
        ROLLBACK;
        RAISE EXCEPTION '%', v_error;
    END IF;
end;
$$;


--------------------------------------------------------


CREATE OR REPLACE PROCEDURE sp_flight_stats(
    p_flight_id INTEGER,
    OUT p_tickets_sold INTEGER,
    OUT p_revenue NUMERIC,
    OUT p_free_seats INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_flight_id IS NULL THEN
        RAISE EXCEPTION 'Flight ID cannot be null';
    end if;

    IF NOT EXISTS(SELECT 1 FROM flight WHERE flight_id = p_flight_id) THEN
        RAISE EXCEPTION 'Flight with this ID does not exist.';
    end if;

    SELECT COUNT(t.ticket_id) AS tickets_sold, COALESCE(SUM(t.final_price), 0), m.model_capacity - COUNT(t.ticket_id)
    INTO p_tickets_sold, p_revenue, p_free_seats
    FROM Flight f
    JOIN Plane p ON p.plane_id = f.plane_id
    JOIN Model m ON m.model_id = p.model_id
    LEFT JOIN Ticket t ON t.flight_id = f.flight_id
    WHERE f.flight_id = p_flight_id
    GROUP BY f.flight_id, m.model_capacity;
end;
$$;