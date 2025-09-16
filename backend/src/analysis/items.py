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

    @property
    def uptime_ghoul(self):
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
        return True


class TrinketPreprocessor(BasePreprocessor):
    TRINKETS = [
        APTrinket("Relic of Xuen", 79327, "Blessing of the Celestials", 15, 55),
        APTrinket("Zen Alchemist Stone", 75274, "Zen Alchemist Stone", 15, 55),
        HasteTrinket("Darkmist Vortex", 87172, "Alacrity", 20, 115),
        HasteTrinket("Darkmist Vortex", 86894, "Alacrity", 20, 115),
        HasteTrinket("Darkmist Vortex", 86336, "Alacrity", 20, 115),
        APTrinket("Lei Shen's Final Orders", 87072, "Unwavering Might", 20, 55),
        APTrinket("Lei Shen's Final Orders", 86144, "Unwavering Might", 20, 55),
        APTrinket("Lei Shen's Final Orders", 86802, "Unwavering Might", 20, 55),
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


# class T15Preprocessor(BasePreprocessor):
#     def __init__(self, combatant_info):
#         self.has_4p = False
#         self._calc_num_t15(combatant_info)

#     def _calc_num_t15(self, combatant_info):
#         count = 0

#         for item in combatant_info.get("gear", []):
#             if item["id"] in {
#                 # Head
#                 65181,
#                 60341,
#                 # Shoulders
#                 65183,
#                 60343,
#                 # Chest
#                 65179,
#                 60339,
#                 # Legs
#                 65182,
#                 60342,
#                 # Hands
#                 65180,
#                 60340,
#             }:
#                 count += 1
#         if count >= 4:
#             self.has_4p = True

#     def preprocess_event(self, event):
#         if event["type"] == "applybuff" and event["ability"] == "Death Eater":
#             self.has_4p = True

#     @property
#     def max_uptime(self):
#         return 0.98


class ItemPreprocessor(BasePreprocessor):
    def __init__(self, combatant_info):
        self._trinkets = TrinketPreprocessor(combatant_info)
        # self._t15 = T15Preprocessor(combatant_info)

        self._processors = [
            self._trinkets,
            # self._t15,
        ]

    def preprocess_event(self, event):
        for processor in self._processors:
            processor.preprocess_event(event)

    def has_trinket(self, buff_name):
        return self._trinkets.has_trinket(buff_name)

    # def has_t14_4p(self):
    #     return self._t15.has_4p

    @property
    def trinkets(self):
        return list(self._trinkets)
