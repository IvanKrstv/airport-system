TRUNCATE TABLE Ticket, Seat, SeatClass, Employee, JobPosition, Flight,
    Plane, Model, Company, Passenger, Destination, Country
    RESTART IDENTITY CASCADE;

INSERT INTO Country (country_name, country_code) VALUES
                 ('Bulgaria', 'BG'),
                 ('Germany', 'DE'),
                 ('United Kingdom', 'GB'),
                 ('France', 'FR'),
                 ('Italy', 'IT'),
                 ('Turkey', 'TR'),
                 ('United States', 'US');

INSERT INTO Destination (city_name, country_id) VALUES
                        ('Sofia', 1),
                        ('Varna', 1),
                        ('London', 3),
                        ('Berlin', 2),
                        ('Paris', 4),
                        ('Rome', 5),
                        ('Istanbul', 6);

INSERT INTO Company (company_name, country_id) VALUES
                   ('Airbus', 4),
                   ('Boeing', 7);

INSERT INTO Model (model_name, model_capacity, company_id) VALUES
               ('A320', 180, 1),
               ('737-800', 189, 2),
               ('A321', 220, 1);

INSERT INTO Plane (model_id, license_plate) VALUES
                (1, 'LZ-AAA'),
                (2, 'LZ-BBA'),
                (3, 'LZ-ABA'),
                (1, 'LZ-AAB');

INSERT INTO SeatClass (seat_class_name, percent_increase) VALUES
                      ('Economy', 0),
                      ('Business', 50),
                      ('First', 100);

INSERT INTO Seat (seat_name, seat_class_id, plane_id) VALUES
              ('1A', 3, 1), ('2A', 2, 1), ('3A', 1, 1), ('3B', 1, 1), ('4A', 1, 1), ('4B', 1, 1),
              ('1A', 3, 2), ('2A', 2, 2), ('3A', 1, 2), ('3B', 1, 2), ('4A', 1, 2), ('4B', 1, 2),
              ('1A', 3, 3), ('2A', 2, 3), ('3A', 1, 3), ('3B', 1, 3), ('4A', 1, 3), ('4B', 1, 3);


INSERT INTO JobPosition (position_name, salary) VALUES
                        ('Ticket Agent', 1800.00),
                        ('Senior Ticket Agent', 2400.00),
                        ('Gate Manager', 3200.00);


INSERT INTO Employee (employee_name, phone_number, position_id) VALUES
                    ('Stefan Todorov', '+359888100001', 1),
                    ('Vesela Koleva', '+359888100002', 1),
                    ('Dimitar Angelov', '+359888100003', 2),
                    ('Kalin Iliev', '+359888100004', 3);


INSERT INTO Passenger (passport_id, passenger_name, country_id) VALUES
                    ('BG1000001', 'Georgi Ivanov', 1),
                    ('BG1000002', 'Maria Dimitrova', 1),
                    ('BG1000003', 'Nikolay Stoyanov', 1),
                    ('BG1000004', 'Elena Georgieva', 1),
                    ('DE2000001', 'Hans Mueller', 2),
                    ('GB3000001', 'James Wilson', 3),
                    ('IT5000001', 'Marco Rossi', 5),
                    ('US1100001', 'Michael Brown', 7);


INSERT INTO Flight (flight_timestamp, price, plane_id, from_destination_id, to_destination_id) VALUES
                   ('2026-09-05 08:30', 180.00, 1, 1, 3),   -- Sofia -> London
                   ('2026-09-12 07:45', 120.00, 2, 2, 4),   -- Varna -> Berlin
                   ('2026-09-26 06:50', 160.00, 3, 1, 5),   -- Sofia -> Paris
                   ('2026-10-10 13:15', 130.00, 1, 1, 6),   -- Sofia -> Rome
                   ('2026-10-24 10:30',  75.00, 2, 1, 7),   -- Sofia -> Istanbul
                   ('2026-12-05 07:10', 165.00, 1, 5, 2);   -- Paris -> Varna


INSERT INTO Ticket (seat_id, flight_id, passenger_id, employee_id, final_price, sold_at) VALUES
                 (1,  1, 1, 1, 360.00, '2026-08-20 10:15'),
                 (3,  1, 2, 2, 180.00, '2026-08-22 14:40'),
                 (2,  1, 3, 2, 270.00, '2026-08-25 09:05'),
                 (9,  2, 4, 3, 120.00, '2026-08-28 11:30'),
                 (8,  2, 1, 3, 180.00, '2026-09-01 09:45'),
                 (15, 3, 2, 1, 160.00, '2026-09-08 15:25'),
                 (13, 3, 5, 4, 320.00, '2026-09-10 10:00'),
                 (16, 3, 1, 1, 160.00, '2026-09-12 08:35'),
                 (5,  4, 6, 2, 130.00, '2026-09-22 11:05'),
                 (2,  4, 2, 4, 195.00, '2026-09-28 14:15'),
                 (11, 5, 4, 1,  75.00, '2026-10-01 16:40'),
                 (7,  5, 6, 3, 150.00, '2026-10-03 13:00');
