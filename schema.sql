DROP TABLE IF EXISTS Ticket, Seat, SeatClass, Employee, JobPosition, Flight,
    Plane, Model, Company, Passenger, Destination, Country CASCADE;

CREATE TABLE Country
(
    country_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_name VARCHAR(30) UNIQUE NOT NULL ,
    country_code CHAR(2) UNIQUE
);

CREATE TABLE Destination
(
    destination_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name VARCHAR(30) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES Country (country_id),
    CONSTRAINT Unique_City_Per_Country UNIQUE (city_name, country_id)
);

CREATE TABLE Passenger
(
    passenger_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    passport_id VARCHAR(20) UNIQUE NOT NULL,
    passenger_name VARCHAR(50) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES Country (country_id)
);

CREATE TABLE Company
(
    company_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_name VARCHAR(30) UNIQUE NOT NULL ,
    country_id INTEGER NOT NULL REFERENCES Country (country_id)
);

CREATE TABLE Model
(
    model_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    model_capacity INTEGER NOT NULL CHECK (model_capacity > 0),
    company_id INTEGER NOT NULL REFERENCES Company (company_id)
);

CREATE TABLE Plane
(
    plane_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES Model (model_id),
    license_plate VARCHAR(10) UNIQUE NOT NULL
);

CREATE TABLE Flight
(
    flight_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flight_timestamp TIMESTAMP NOT NULL ,
    price NUMERIC(10,2) NOT NULL CHECK (price > 0),
    plane_id INTEGER NOT NULL REFERENCES Plane (plane_id),
    from_destination_id INTEGER NOT NULL REFERENCES Destination (destination_id),
    to_destination_id INTEGER NOT NULL REFERENCES Destination (destination_id),
    CONSTRAINT check_flight_route CHECK (from_destination_id <> to_destination_id)
);

CREATE TABLE JobPosition
(
    position_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    position_name VARCHAR(30) UNIQUE NOT NULL,
    salary NUMERIC(10,2) NOT NULL CHECK (salary > 0)
);

CREATE TABLE Employee
(
    employee_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(13) UNIQUE NOT NULL,
    position_id INTEGER NOT NULL REFERENCES JobPosition (position_id)
);

CREATE TABLE SeatClass
(
    seat_class_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seat_class_name VARCHAR(20) UNIQUE NOT NULL,
    percent_increase INTEGER NOT NULL CHECK (percent_increase >= 0)
);

CREATE TABLE Seat
(
    seat_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seat_name VARCHAR(10) NOT NULL,
    seat_class_id INTEGER NOT NULL REFERENCES SeatClass (seat_class_id),
    plane_id INTEGER NOT NULL REFERENCES Plane (plane_id),
    CONSTRAINT Unique_Seat_Per_Plane UNIQUE (plane_id, seat_name)
);

CREATE TABLE Ticket
(
    ticket_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seat_id INTEGER NOT NULL REFERENCES Seat (seat_id),
    flight_id INTEGER NOT NULL REFERENCES Flight (flight_id),
    passenger_id INTEGER NOT NULL REFERENCES Passenger (passenger_id),
    employee_id INTEGER NOT NULL REFERENCES Employee (employee_id),
    final_price NUMERIC(10,2) NOT NULL CHECK (final_price > 0),
    sold_at TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT Unique_Seat_Per_Flight UNIQUE (seat_id, flight_id)
);