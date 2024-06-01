from analysis.base import BasePreprocessor


class Trinket:
    def __init__(self, name, item_id, buff_name, proc_duration, proc_cd, on_use=False):
        self.name = name
        self.item_id = item_id
        self.buff_name = buff_name
        self.proc_duration = proc_duration * 1000
        self.proc_cd = proc_cd * 1000
        self.on_use = on_use
        self.icon = None

    @property
    def snapshots_gargoyle(self):
        raise NotImplementedError

    @property
    def snapshots_army_haste(self):
        raise NotImplementedError


class APTrinket(Trinket):
    @property
    def snapshots_gargoyle(self):
        return True

    @property
    def snapshots_army_haste(self):
        return False


class HasteTrinket(Trinket):
    @property
    def snapshots_gargoyle(self):
        return False

    @property
    def snapshots_army_haste(self):
        return True


class TrinketPreprocessor(BasePreprocessor):
    TRINKETS = [
        APTrinket("Darkmoon Card: Greatness", 42987, "Greatness", 15, 45),
        APTrinket("Wrathstone", 45263, "Wrathstone", 20, 120, on_use=True),
        APTrinket("Blood of the Old God", 45522, "Blood of the Old God", 10, 50),
        APTrinket("Pyrite Infuser", 45286, "Pyrite Infusion", 10, 50),
        APTrinket("Mirror of Truth", 40684, "Reflection of Torment", 10, 50),
        APTrinket("Death's Choice", 47464, "Paragon", 15, 45),
        APTrinket("Death's Choice", 47303, "Paragon", 15, 45),
        APTrinket("Death's Verdict", 47131, "Paragon", 15, 45),
        APTrinket("Death's Verdict", 47115, "Paragon", 15, 45),
        APTrinket("Victor's Call", 47725, "Rising Fury", 20, 120, on_use=True),
        APTrinket("Victor's Call", 47948, "Rising Fury", 20, 120, on_use=True),
        APTrinket(
            "Vengeance of the Forsaken", 47881, "Rising Fury", 20, 120, on_use=True
        ),
        APTrinket(
            "Vengeance of the Forsaken", 48020, "Rising Fury", 20, 120, on_use=True
        ),
        APTrinket("Mark of Supremacy", 47734, "Rage", 20, 120, on_use=True),
        HasteTrinket(
            "Mark of Norgannon", 40531, "Mark of Norgannon", 20, 120, on_use=True
        ),
        HasteTrinket("Comet's Trail", 45609, "Comet's Trail", 10, 45),
        HasteTrinket("Meteorite Whetstone", 37390, "Meteorite Whetstone", 10, 45),
        HasteTrinket(
            "Shard of the Crystal Heart", 48722, "Celerity", 20, 120, on_use=True
        ),
    ]
    TRINKET_MAP = {trinket.item_id: trinket for trinket in TRINKETS}
    TRINKEY_MAP_BY_BUFF_NAME = {trinket.buff_name: trinket for trinket in TRINKETS}

    def __init__(self, combatant_info):
        self._trinkets = self._parse_trinkets(combatant_info)
        self._trinkets_by_buff_name = {
            trinket.buff_name: trinket for trinket in self._trinkets
        }

    def _parse_trinkets(self, combatant_info):
        trinkets = []

        for item in combatant_info.get("gear", []):
            trinket = self.TRINKET_MAP.get(item["id"])
            if trinket:
                trinket.icon = item["item_icon"]
                trinkets.append(trinket)
        return trinkets

    def preprocess_event(self, event):
        if (
            event["type"] == "applybuff"
            and event["ability"] in self.TRINKEY_MAP_BY_BUFF_NAME
        ):
            trinket = self.TRINKEY_MAP_BY_BUFF_NAME[event["ability"]]

            if event["ability"] not in self._trinkets_by_buff_name:
                trinket.icon = event["ability_icon"]
                self._trinkets.append(trinket)
                self._trinkets_by_buff_name = {
                    trinket.buff_name: trinket for trinket in self._trinkets
                }

    def has_trinket(self, buff_name):
        return buff_name in self._trinkets_by_buff_name

    def __iter__(self):
        return iter(self._trinkets)

    def __len__(self):
        return len(self._trinkets)


class T11Preprocessor(BasePreprocessor):
    def __init__(self, combatant_info):
        self.has_4p = False
        self._calc_num_t11(combatant_info)

    def _calc_num_t11(self, combatant_info):
        count = 0

        for item in combatant_info.get("gear", []):
            if item["id"] in {
                # Head
                65181,
                60341,
                # Shoulders
                65183,
                60343,
                # Chest
                65179,
                60339,
                # Legs
                65182,
                60342,
                # Hands
                65180,
                60340,
            }:
                count += 1
        if count >= 4:
            self.has_4p = True

    def preprocess_event(self, event):
        if event["type"] == "applybuff" and event["ability"] == "Death Eater":
            self.has_4p = True

    @property
    def max_uptime(self):
        return 0.98

class T12Preprocessor(BasePreprocessor):
    def __init__(self, combatant_info):
        self.has_2p = False
        self._calc_num_t12(combatant_info)

    def _calc_num_t12(self, combatant_info):
        count = 0
        for item in combatant_info.get("gear", []):
            if item["id"] in {
                # Head
                71478,
                71060,
                # Shoulders
                71480,
                71062,
                # Chest
                71058,
                71476,
                # Legs
                71479,
                71061,
                # Hands
                71477,
                71059,
            }:
                count += 1
        if count >= 2:
            self.has_2p = True

    def preprocess_event(self, event):
        if event["type"] == "applybuff" and event["ability"] == "Smoldering Rune":
            self.has_2p = True

    @property
    def max_uptime(self):
        return 0.98

class ItemPreprocessor(BasePreprocessor):
    def __init__(self, combatant_info):
        self._trinkets = TrinketPreprocessor(combatant_info)
        self._t11 = T11Preprocessor(combatant_info)
        self._t12 = T12Preprocessor(combatant_info)

        self._processors = [
            self._trinkets,
            self._t11,
            self._t12,
        ]

    def preprocess_event(self, event):
        for processor in self._processors:
            processor.preprocess_event(event)

    def has_trinket(self, buff_name):
        return self._trinkets.has_trinket(buff_name)

    def t11_max_uptime(self):
        return self._t11.max_uptime

    def t12_max_uptime(self):
        return self._t12.max_uptime

    @property
    def trinkets(self):
        return list(self._trinkets)
