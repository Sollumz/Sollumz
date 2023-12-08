from enum import IntEnum

class Flashiness(IntEnum):
    CONSTANT = 0
    RANDOM = 1
    RANDOM_OVERRIDE_IF_WET = 2
    ONCE_PER_SECOND = 3
    TWICE_PER_SECOND = 4
    FIVE_PER_SECOND = 5
    RANDOM_FLASHINESS = 6
    OFF = 7
    UNUSED = 8
    ALARM = 9
    ON_WHEN_RAINING = 10
    CYCLE_1 = 11
    CYCLE_2 = 12
    CYCLE_3 = 13
    DISCO = 14
    CANDLE = 15
    PLANE = 16
    FIRE = 17
    THRESHOLD = 18
    ELECTRIC = 19
    STROBE = 20

LightFlashinessEnumItems = tuple((enum.name, f"{label} ({enum.value})", desc, enum.value) for enum, label, desc in (
    (Flashiness.CONSTANT, "Constant", "Constant lighting without flashing"),
    (Flashiness.RANDOM, "Random", "Light flashes randomly"),
    (Flashiness.RANDOM_OVERRIDE_IF_WET, "Random Override If Wet", "Randomly flash if the light is wet"),
    (Flashiness.ONCE_PER_SECOND, "Once Per Second", "Flash once per second"),
    (Flashiness.TWICE_PER_SECOND, "Twice Per Second", "Flash twice per second"),
    (Flashiness.FIVE_PER_SECOND, "Five Per Second", "Flash five times per second"),
    (Flashiness.RANDOM_FLASHINESS, "Random Flashiness", "Flashes Randomly"),
    (Flashiness.OFF, "Off", "Turns Light Off"),
    (Flashiness.UNUSED, "Unused", "Unused"),
    (Flashiness.ALARM, "Alarm", "Flash like an alarm siren"),
    (Flashiness.ON_WHEN_RAINING, "On When Raining", "Flash only when raining"),
    (Flashiness.CYCLE_1, "Cycle 1", "Cycle 1"),
    (Flashiness.CYCLE_2, "Cycle 2", "Cycle 2"),
    (Flashiness.CYCLE_3, "Cycle 3", "Cycle 3"),
    (Flashiness.DISCO, "Disco", "Flash like a disco light"),
    (Flashiness.CANDLE, "Candle", "Flash like a candle flame"),
    (Flashiness.PLANE, "Plane", "Flash like a plane landing strip(?)"),
    (Flashiness.FIRE, "Fire", "Flash like a flame"),
    (Flashiness.THRESHOLD, "Threshold", "Threshold"),
    (Flashiness.ELECTRIC, "Electric", "Electric"),
    (Flashiness.STROBE, "Strobe", "Flash like a strobe light")
))
