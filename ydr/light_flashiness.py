from szio.gta5 import LightFlashiness

LightFlashinessEnumItems = tuple((enum.name, f"{label} ({enum.value})", desc, enum.value) for enum, label, desc in (
    (LightFlashiness.CONSTANT, "Constant", "Constant lighting without flashing"),
    (LightFlashiness.RANDOM, "Random", "Light flashes randomly"),
    (LightFlashiness.RANDOM_OVERRIDE_IF_WET, "Random Override If Wet", "Randomly flash if the light is wet"),
    (LightFlashiness.ONCE_PER_SECOND, "Once Per Second", "Flash once per second"),
    (LightFlashiness.TWICE_PER_SECOND, "Twice Per Second", "Flash twice per second"),
    (LightFlashiness.FIVE_PER_SECOND, "Five Per Second", "Flash five times per second"),
    (LightFlashiness.RANDOM_FLASHINESS, "Random Flashiness", "Flashes Randomly"),
    (LightFlashiness.OFF, "Off", "Turns Light Off"),
    (LightFlashiness.UNUSED, "Unused", "Unused"),
    (LightFlashiness.ALARM, "Alarm", "Flash like an alarm siren"),
    (LightFlashiness.ON_WHEN_RAINING, "On When Raining", "Flash only when raining"),
    (LightFlashiness.CYCLE_1, "Cycle 1", "Cycle 1"),
    (LightFlashiness.CYCLE_2, "Cycle 2", "Cycle 2"),
    (LightFlashiness.CYCLE_3, "Cycle 3", "Cycle 3"),
    (LightFlashiness.DISCO, "Disco", "Flash like a disco light"),
    (LightFlashiness.CANDLE, "Candle", "Flash like a candle flame"),
    (LightFlashiness.PLANE, "Plane", "Flash like a plane landing strip(?)"),
    (LightFlashiness.FIRE, "Fire", "Flash like a flame"),
    (LightFlashiness.THRESHOLD, "Threshold", "Threshold"),
    (LightFlashiness.ELECTRIC, "Electric", "Electric"),
    (LightFlashiness.STROBE, "Strobe", "Flash like a strobe light")
))
