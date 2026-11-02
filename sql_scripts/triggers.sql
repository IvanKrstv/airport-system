-- Integrity triggers: a ticket's seat must always belong to the plane of its flight.
-- Safe to re-run (does not touch data). Run after schema.sql.


-- 1) A flight with sold tickets cannot be moved to another plane
CREATE OR REPLACE FUNCTION trg_flight_plane_locked()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.plane_id <> OLD.plane_id
       AND EXISTS (SELECT 1 FROM Ticket WHERE flight_id = OLD.flight_id) THEN
        RAISE EXCEPTION 'Cannot change the plane of flight % - it already has sold tickets.', OLD.flight_id;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS flight_plane_locked ON Flight;
CREATE TRIGGER flight_plane_locked
    BEFORE UPDATE OF plane_id ON Flight
    FOR EACH ROW EXECUTE FUNCTION trg_flight_plane_locked();


--------------------------------------------------------


-- 2) A seat that has been sold cannot be moved to another plane
CREATE OR REPLACE FUNCTION trg_seat_plane_locked()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.plane_id <> OLD.plane_id
       AND EXISTS (SELECT 1 FROM Ticket WHERE seat_id = OLD.seat_id) THEN
        RAISE EXCEPTION 'Cannot change the plane of seat % - it has already been sold.', OLD.seat_name;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS seat_plane_locked ON Seat;
CREATE TRIGGER seat_plane_locked
    BEFORE UPDATE OF plane_id ON Seat
    FOR EACH ROW EXECUTE FUNCTION trg_seat_plane_locked();


--------------------------------------------------------


-- 3) A ticket's seat must be on the plane that operates the flight
--    (also covers tickets inserted outside sell_ticket, e.g. manually or from seed.sql)
CREATE OR REPLACE FUNCTION trg_ticket_seat_matches_flight()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM Flight f
        JOIN Seat s ON s.plane_id = f.plane_id
        WHERE f.flight_id = NEW.flight_id
          AND s.seat_id = NEW.seat_id
    ) THEN
        RAISE EXCEPTION 'Seat % is not on the plane of flight %.', NEW.seat_id, NEW.flight_id;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ticket_seat_matches_flight ON Ticket;
CREATE TRIGGER ticket_seat_matches_flight
    BEFORE INSERT OR UPDATE OF seat_id, flight_id ON Ticket
    FOR EACH ROW EXECUTE FUNCTION trg_ticket_seat_matches_flight();
