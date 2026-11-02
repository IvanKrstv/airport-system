from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str                       # име на колоната в базата
    label: str                      # заглавие в интерфейса (в една таблица са уникални)
    type: str                       # 'text' | 'int' | 'decimal' | 'datetime' | 'fk'
    ref: str | None = None          # за 'fk': ключът на таблицата, към която сочи
    max_len: int | None = None      # за 'text': максимална дължина
    min_value: float | None = None  # за 'int' и 'decimal': минимална стойност
    nullable: bool = False          # за 'text': разрешено ли е празно (NULL)


@dataclass(frozen=True)
class Table:
    name: str                       # име на таблицата в базата (малки букви)
    label: str                      # име в интерфейса
    pk: str                         # първичен ключ
    # SQL израз с псевдоним {a}: как се показва един ред в падащите менюта и в колоните с foreign key (вместо number-ID)
    label_sql: str
    columns: tuple[Column, ...]
    can_edit: bool = True
    can_delete: bool = True


_FLIGHT_LABEL = (
    "to_char({a}.flight_timestamp, 'YYYY-MM-DD HH24:MI') || ' ' || "
    "(SELECT d.city_name FROM destination d WHERE d.destination_id = {a}.from_destination_id)"
    " || ' → ' || "
    "(SELECT d.city_name FROM destination d WHERE d.destination_id = {a}.to_destination_id)"
    " || ' (#' || {a}.flight_id || ')'"
)

_SEAT_LABEL = (
    "{a}.seat_name || ' (' || "
    "(SELECT p.license_plate FROM plane p WHERE p.plane_id = {a}.plane_id) || ')'"
)

TABLES: dict[str, Table] = {t.name: t for t in (
    Table('country', 'Countries', 'country_id', '{a}.country_name', (
        Column('country_name', 'Country', 'text', max_len=30),
        Column('country_code', 'Code (2 letters)', 'text', max_len=2, nullable=True),
    )),
    Table('destination', 'Destinations', 'destination_id', '{a}.city_name', (
        Column('city_name', 'City', 'text', max_len=30),
        Column('country_id', 'Country', 'fk', ref='country'),
    )),
    Table('company', 'Manufacturers', 'company_id', '{a}.company_name', (
        Column('company_name', 'Manufacturer', 'text', max_len=30),
        Column('country_id', 'Country', 'fk', ref='country'),
    )),
    Table('model', 'Aircraft models', 'model_id', '{a}.model_name', (
        Column('model_name', 'Model', 'text', max_len=50),
        Column('model_capacity', 'Capacity', 'int', min_value=1),
        Column('company_id', 'Manufacturer', 'fk', ref='company'),
    )),
    Table('plane', 'Planes', 'plane_id', '{a}.license_plate', (
        Column('model_id', 'Model', 'fk', ref='model'),
        Column('license_plate', 'Registration', 'text', max_len=10),
    )),
    Table('seatclass', 'Seat classes', 'seat_class_id', '{a}.seat_class_name', (
        Column('seat_class_name', 'Class', 'text', max_len=20),
        Column('percent_increase', 'Surcharge (%)', 'int', min_value=0),
    )),
    Table('seat', 'Seats', 'seat_id', _SEAT_LABEL, (
        Column('seat_name', 'Seat', 'text', max_len=10),
        Column('seat_class_id', 'Class', 'fk', ref='seatclass'),
        Column('plane_id', 'Plane', 'fk', ref='plane'),
    )),
    Table('jobposition', 'Job positions', 'position_id', '{a}.position_name', (
        Column('position_name', 'Position', 'text', max_len=30),
        Column('salary', 'Salary', 'decimal', min_value=0.01),
    )),
    Table('employee', 'Employees', 'employee_id', '{a}.employee_name', (
        Column('employee_name', 'Name', 'text', max_len=50),
        Column('phone_number', 'Phone', 'text', max_len=13),
        Column('position_id', 'Position', 'fk', ref='jobposition'),
    )),
    Table('passenger', 'Passengers', 'passenger_id',
          "{a}.passenger_name || ' (' || {a}.passport_id || ')'", (
        Column('passport_id', 'Passport', 'text', max_len=20),
        Column('passenger_name', 'Name', 'text', max_len=50),
        Column('country_id', 'Country', 'fk', ref='country'),
    )),
    Table('flight', 'Flights', 'flight_id', _FLIGHT_LABEL, (
        Column('flight_timestamp', 'Departure', 'datetime'),
        Column('price', 'Price', 'decimal', min_value=0.01),
        Column('plane_id', 'Plane', 'fk', ref='plane'),
        Column('from_destination_id', 'From', 'fk', ref='destination'),
        Column('to_destination_id', 'To', 'fk', ref='destination'),
    )),
    Table('ticket', 'Tickets', 'ticket_id', "'#' || {a}.ticket_id", (
        Column('seat_id', 'Seat', 'fk', ref='seat'),
        Column('flight_id', 'Flight', 'fk', ref='flight'),
        Column('passenger_id', 'Passenger', 'fk', ref='passenger'),
        Column('employee_id', 'Employee', 'fk', ref='employee'),
        Column('final_price', 'Price', 'decimal', min_value=0.01),
        Column('sold_at', 'Sold at', 'datetime'),
    ), can_edit=False, can_delete=False),
)}
