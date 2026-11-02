"""Описание на таблиците за универсалния CRUD.

Тук е единственото място, което знае как изглежда всяка таблица. Ако добавиш
нова таблица или колона в базата, добавяш я и тук - формите и списъците се
оправят сами.
"""
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
    # SQL израз с псевдоним {a}: как се показва един ред в падащите менюта
    # и в колоните с външен ключ (вместо number-ID)
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
    Table('country', 'Държави', 'country_id', '{a}.country_name', (
        Column('country_name', 'Държава', 'text', max_len=30),
        Column('country_code', 'Код (2 букви)', 'text', max_len=2, nullable=True),
    )),
    Table('destination', 'Дестинации', 'destination_id', '{a}.city_name', (
        Column('city_name', 'Град', 'text', max_len=30),
        Column('country_id', 'Държава', 'fk', ref='country'),
    )),
    Table('company', 'Производители', 'company_id', '{a}.company_name', (
        Column('company_name', 'Производител', 'text', max_len=30),
        Column('country_id', 'Държава', 'fk', ref='country'),
    )),
    Table('model', 'Модели самолети', 'model_id', '{a}.model_name', (
        Column('model_name', 'Модел', 'text', max_len=50),
        Column('model_capacity', 'Капацитет', 'int', min_value=1),
        Column('company_id', 'Производител', 'fk', ref='company'),
    )),
    Table('plane', 'Самолети', 'plane_id', '{a}.license_plate', (
        Column('model_id', 'Модел', 'fk', ref='model'),
        Column('license_plate', 'Регистрация', 'text', max_len=10),
    )),
    Table('seatclass', 'Класове места', 'seat_class_id', '{a}.seat_class_name', (
        Column('seat_class_name', 'Клас', 'text', max_len=20),
        Column('percent_increase', 'Надбавка (%)', 'int', min_value=0),
    )),
    Table('seat', 'Места', 'seat_id', _SEAT_LABEL, (
        Column('seat_name', 'Място', 'text', max_len=10),
        Column('seat_class_id', 'Клас', 'fk', ref='seatclass'),
        Column('plane_id', 'Самолет', 'fk', ref='plane'),
    )),
    Table('jobposition', 'Длъжности', 'position_id', '{a}.position_name', (
        Column('position_name', 'Длъжност', 'text', max_len=30),
        Column('salary', 'Заплата', 'decimal', min_value=0.01),
    )),
    Table('employee', 'Служители', 'employee_id', '{a}.employee_name', (
        Column('employee_name', 'Име', 'text', max_len=50),
        Column('phone_number', 'Телефон', 'text', max_len=13),
        Column('position_id', 'Длъжност', 'fk', ref='jobposition'),
    )),
    Table('passenger', 'Пътници', 'passenger_id',
          "{a}.passenger_name || ' (' || {a}.passport_id || ')'", (
        Column('passport_id', 'Паспорт', 'text', max_len=20),
        Column('passenger_name', 'Име', 'text', max_len=50),
        Column('country_id', 'Държава', 'fk', ref='country'),
    )),
    Table('flight', 'Полети', 'flight_id', _FLIGHT_LABEL, (
        Column('flight_timestamp', 'Излитане', 'datetime'),
        Column('price', 'Цена', 'decimal', min_value=0.01),
        Column('plane_id', 'Самолет', 'fk', ref='plane'),
        Column('from_destination_id', 'От', 'fk', ref='destination'),
        Column('to_destination_id', 'До', 'fk', ref='destination'),
    )),
    Table('ticket', 'Билети', 'ticket_id', "'#' || {a}.ticket_id", (
        Column('seat_id', 'Място', 'fk', ref='seat'),
        Column('flight_id', 'Полет', 'fk', ref='flight'),
        Column('passenger_id', 'Пътник', 'fk', ref='passenger'),
        Column('employee_id', 'Служител', 'fk', ref='employee'),
        Column('final_price', 'Цена', 'decimal', min_value=0.01),
        Column('sold_at', 'Продаден на', 'datetime'),
    ), can_edit=False, can_delete=False),
)}
