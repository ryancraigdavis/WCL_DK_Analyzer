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

    # @property
    # def snapshots_army_haste(self):
    #     raise NotImplementedError


class APTrinket(Trinket):
    @property
    def snapshots_gargoyle(self):
        return True

    # @property
    # def snapshots_army_haste(self):
    #     return False


class HasteTrinket(Trinket):
    @property
    def uptime_ghoul(self):
        return True

    @property
    def snapshots_gargoyle(self):
        return False

class TrinketPreprocessor(BasePreprocessor):
    TRINKETS = [
        APTrinket("Right Eye of Rajh", 56100, "Eye of Doom", 10, 50),
        APTrinket("Right Eye of Rajh", 56431, "Eye of Doom", 10, 50),
        APTrinket("Heart of Rage", 65072, "Rageheart", 20, 100),
        APTrinket("Heart of Rage", 59224, "Rageheart", 20, 100),
        APTrinket("License to Slay", 58180, "Slayer", 15, 100),
        APTrinket("Impatience of Youth", 62464, "Thrill of Victory", 20, 120, on_use=True),
        APTrinket("Impatience of Youth", 62469, "Thrill of Victory", 20, 120, on_use=True),
        APTrinket("Might of the Ocean", 56285, "Typhoon", 15, 90, on_use=True),
        APTrinket("Might of the Ocean", 55251, "Typhoon", 15, 90, on_use=True),
        APTrinket("Magnetite Mirror", 56345, "Polarization", 15, 90, on_use=True),
        APTrinket("Magnetite Mirror", 55814, "Polarization", 15, 90, on_use=True),
        APTrinket("King of Boars", 52351, "King of Boars", 20, 120, on_use=True),
        APTrinket("Fury of Angerforge", 59461, "Forged Fury", 20, 120, on_use=True),
        APTrinket("Heart of Solace", 56393, "Heartened", 20, 100),
        APTrinket("Heart of Solace", 55868, "Heartened", 20, 100),
        HasteTrinket("Crushing Weight", 65118, "Race Against Death", 15, 75),
        HasteTrinket("Crushing Weight", 59506, "Race Against Death", 15, 75),
        HasteTrinket("Shrine-Cleansing Purifier", 63838, "Fatality", 20, 100),
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

    def has_t11_4p(self):
        return self._t11.has_4p

    def has_t12_2p(self):
        return self._t12.has_2p

    def t11_max_uptime(self):
        return self._t11.max_uptime

    def t12_max_uptime(self):
        return self._t12.max_uptime

    @property
    def trinkets(self):
        return list(self._trinkets)
