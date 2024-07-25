from collections import defaultdict
from typing import List
# import os
import json

from analysis.base import (
    AnalysisScorer,
    BaseAnalyzer,
    ScoreWeight,
    calculate_uptime,
    combine_windows,
    Window,
)
from analysis.core_analysis import (
    BombAnalyzer,
    BuffTracker,
    CoreAnalysisConfig,
    SynapseSpringsAnalyzer,
    RPAnalyzer,
    RuneTracker,
    MeleeUptimeAnalyzer,
    TrinketAnalyzer,
    BuffUptimeAnalyzer,
    T11UptimeAnalyzer,
    T12UptimeAnalyzer,
)
from analysis.items import ItemPreprocessor
from report import Fight


class DebuffUptimeAnalyzer(BaseAnalyzer):
    class WindowManager:
        def __init__(self, end_time):
            self._windows_by_target = defaultdict(list)
            self._window_by_target = {}
            self._end_time = end_time

        def add_window(self, target, start, end=None):
            window = Window(start, end)
            self._window_by_target[target] = window
            self._windows_by_target[target].append(window)

        def end_window(self, target, end):
            window = self._window_by_target.get(target)
            if window:
                window.end = end

        def has_active_window(self, target):
            window = self._window_by_target.get(target)
            return window and window.end is None

        def coalesce(self):
            windows = [
                window
                for windows in self._windows_by_target.values()
                for window in windows
            ]

            for window in windows:
                if window.end is None:
                    window.end = self._end_time

            return combine_windows(windows)

    def __init__(self, end_time, debuff_name, ignore_windows):
        self._debuff_name = debuff_name
        self._end_time = end_time
        self._ignore_windows = ignore_windows
        self._wm = self.WindowManager(end_time)

    def add_event(self, event):
        if event["type"] not in ("applydebuff", "removedebuff", "refreshdebuff"):
            return

        if event["ability"] != self._debuff_name:
            return

        if event["type"] in ("applydebuff", "refreshdebuff"):
            if not self._wm.has_active_window(event["target"]):
                self._wm.add_window(event["target"], event["timestamp"])
        elif event["type"] == "removedebuff":
            self._wm.end_window(event["target"], event["timestamp"])

    def uptime(self):
        windows = self._wm.coalesce()

        return calculate_uptime(
            windows,
            self._ignore_windows,
            self._end_time,
        )

    def score(self):
        return self.uptime()


class BloodPlagueAnalyzer(DebuffUptimeAnalyzer):
    def __init__(self, end_time, ignore_windows):
        super().__init__(end_time, "Blood Plague", ignore_windows)

    def report(self):
        return {
            "blood_plague_uptime": self.uptime(),
        }


class FrostFeverAnalyzer(DebuffUptimeAnalyzer):
    def __init__(self, end_time, ignore_windows):
        super().__init__(end_time, "Frost Fever", ignore_windows)

    def report(self):
        return {
            "frost_fever_uptime": self.uptime(),
        }


class DarkTransformationUptimeAnalyzer(BuffUptimeAnalyzer):
    INCLUDE_PET_EVENTS = True

    def __init__(self, duration, buff_tracker, ignore_windows, items):
        super().__init__(duration, buff_tracker, ignore_windows, "Dark Transformation")

    @property
    def max_uptime(self):
        return .7

    def score(self):
        return min(1, self.uptime() / self.max_uptime)

    def report(self):
        return {
            "dark_transformation_uptime": self.uptime(),
            "dark_transformation_max_uptime": self.max_uptime,
        }

class DarkTransformationWindow(Window):
    def __init__(
        self,
        start,
        fight_duration,
        buff_tracker: BuffTracker,
        ignore_windows,
        items: ItemPreprocessor,
    ):
        self.start = start
        self.end = min(start + 30000, fight_duration)
        self._dark_transformation_first_attack = None

        self._bl_uptime = BuffUptimeAnalyzer(
            self.end, buff_tracker, ignore_windows, {"Bloodlust", "Heroism", "Time Warp"}, self.start
        ) if buff_tracker.has_bl else None
        self._synapse_springs_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Synapse Springs",
            self.start,
            max_duration=10000 - 25,
        ) if buff_tracker.has_synapse_springs else None
        self._crushing_weight_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Race Against Death",
            self.start,
            max_duration=15000 - 25,
        ) if buff_tracker.has_crushing_weight else None
        self._potion_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Golem's Strength",
            self.start,
            max_duration=25000 - 25,
        ) if buff_tracker.has_potion else None
        self._shrine_purifying_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Fatality",
            self.start,
            max_duration=20000 - 25,
        ) if buff_tracker.has_fatality else None
        self._unholy_frenzy_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Unholy Frenzy",
            self.start,
            max_duration=30000 - 25,
        ) if buff_tracker.has_unholy_frenzy else None
        self._berserking_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Berserking",
            self.start,
            max_duration=10000 - 25,
        ) if buff_tracker.has_berserking else None
        self._bloodfury_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Blood Fury",
            self.start,
            max_duration=15000 - 25,
        ) if buff_tracker.has_bloodfury else None
        self._fallen_crusader_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Unholy Strength",
            self.start,
            max_duration=15000 - 25,
        ) if buff_tracker.has_fallen_crusader else None


        self._uptimes = []
        if self._berserking_uptime:
            self._uptimes.append(self._berserking_uptime)
        if self._bloodfury_uptime:
            self._uptimes.append(self._bloodfury_uptime)
        if self._synapse_springs_uptime:
            self._uptimes.append(self._synapse_springs_uptime)
        if self._potion_uptime:
            self._uptimes.append(self._potion_uptime)
        if self._bl_uptime:
            self._uptimes.append(self._bl_uptime)
        if self._unholy_frenzy_uptime:
            self._uptimes.append(self._unholy_frenzy_uptime)
        if self._crushing_weight_uptime:
            self._uptimes.append(self._crushing_weight_uptime)
        if self._shrine_purifying_uptime:
            self._uptimes.append(self._shrine_purifying_uptime)
        if self._fallen_crusader_uptime:
            self._uptimes.append(self._fallen_crusader_uptime)

        self.num_attacks = 0
        self.total_damage = 0
        self._items = items
        self._uptime_trinkets = []
        self.trinket_uptimes = []

        for trinket in self._items.trinkets:
            if trinket.uptime_ghoul:
                self._uptime_trinkets.append(trinket)

        for uptime_trinket in self._uptime_trinkets:
            uptime = BuffUptimeAnalyzer(
                self.end,
                buff_tracker,
                ignore_windows,
                uptime_trinket.buff_name,
                self.start,
                max_duration=uptime_trinket.proc_duration - 25,
            )

            self._uptimes.append(uptime)
            self.trinket_uptimes.append(
                {
                    "trinket": uptime_trinket,
                    "uptime": uptime,
                    "duration": uptime_trinket.proc_duration,
                }
            )

    @property
    def unholy_frenzy_uptime(self):
        return self._unholy_frenzy_uptime.uptime() if self._unholy_frenzy_uptime else None

    @property
    def synapse_springs_uptime(self):
        return self._synapse_springs_uptime.uptime() if self._synapse_springs_uptime else None

    @property
    def potion_uptime(self):
        return self._potion_uptime.uptime() if self._potion_uptime else None

    @property
    def bl_uptime(self):
        return self._bl_uptime.uptime() if self._bl_uptime else None

    @property
    def crushing_weight_uptime(self):
        return self._crushing_weight_uptime.uptime() if self._crushing_weight_uptime else None

    @property
    def shrine_purifying_uptime(self):
        return self._shrine_purifying_uptime.uptime() if self._shrine_purifying_uptime else None

    @property
    def berserking_uptime(self):
        return self._berserking_uptime.uptime() if self._berserking_uptime else None

    @property
    def bloodfury_uptime(self):
        return self._bloodfury_uptime.uptime() if self._bloodfury_uptime else None

    @property
    def fallen_crusader_uptime(self):
        return self._fallen_crusader_uptime.uptime() if self._fallen_crusader_uptime else None

    def _set_dark_transformation_first_attack(self, event):
        self._dark_transformation_first_attack = event["timestamp"]
        for uptime in self._uptimes:
            uptime.set_start_time(event["timestamp"])

    def add_event(self, event):
        for uptime in self._uptimes:
            uptime.add_event(event)

        if "Ghoul" in event["source"] and event["type"] == "damage":
            self.num_attacks += 1
            self.total_damage += event["amount"]

    def score(self):
        dark_transformation_score = ScoreWeight.calculate(
            ScoreWeight(self.berserking_uptime or 0, self.berserking_uptime or 0),
            ScoreWeight(self.bloodfury_uptime or 0, self.bloodfury_uptime or 0),
            ScoreWeight(self.potion_uptime or 0, 3 if self.potion_uptime else 0),
            ScoreWeight(self.synapse_springs_uptime or 0, 3 if self.synapse_springs_uptime else 0),
            ScoreWeight(self.fallen_crusader_uptime or 0, 3 if self.fallen_crusader_uptime else 0),
            ScoreWeight(self.unholy_frenzy_uptime or 0, 10 if self.unholy_frenzy_uptime else 0),
            ScoreWeight(self.bl_uptime or 0, 10 if self.bl_uptime else 0),
            ScoreWeight(
                sum([t["uptime"].uptime() for t in self.trinket_uptimes if t["uptime"].uptime() > 0]) / 
                (sum(1 for t in self.trinket_uptimes if t["uptime"].uptime() > 0) or 1),
                sum(2 for t in self.trinket_uptimes if t["uptime"].uptime() > 0),
            ),
        )
        return dark_transformation_score


class DarkTransformationAnalyzer(BaseAnalyzer):
    INCLUDE_PET_EVENTS = True

    def __init__(self, fight_duration, buff_tracker, ignore_windows, items):
        self.windows: List[DarkTransformationWindow] = []
        self._window = None
        self._buff_tracker = buff_tracker
        self._fight_duration = fight_duration
        self._ignore_windows = ignore_windows
        self._items = items

    def add_event(self, event):
        if event["type"] == "applybuff" and event["ability"] == "Dark Transformation":
            self._window = DarkTransformationWindow(
                event["timestamp"],
                self._fight_duration,
                self._buff_tracker,
                self._ignore_windows,
                self._items,
            )
            self.windows.append(self._window)
        elif self._window and event["timestamp"] <= self._window.end:
            self._window.add_event(event)
        else:
            self._window = None


    @property
    def possible_dark_transformations(self):
        return max(1 + (self._fight_duration - 10000) // 40000, len(self.windows))

    def score(self):
        window_score = sum(window.score() for window in self.windows)
        return ScoreWeight.calculate(
            ScoreWeight(
                window_score / self.possible_dark_transformations, 5 * self.possible_dark_transformations
            ),
        )

    def report(self):
        return {
            "dark_transformation": {
                "score": self.score(),
                "num_possible": self.possible_dark_transformations,
                "num_actual": len(self.windows),
                "bloodlust_uptime": next(
                    (window.bl_uptime for window in self.windows if window.bl_uptime),
                    0,
                ),
                "average_damage": (
                    sum(window.total_damage for window in self.windows)
                    / len(self.windows)
                    if self.windows
                    else 0
                ),
                "windows": [
                    {
                        "score": window.score(),
                        "damage": window.total_damage,
                        "bloodlust_uptime": window.bl_uptime,
                        "num_attacks": window.num_attacks,
                        "synapse_springs_uptime": window.synapse_springs_uptime,
                        "potion_uptime": window.potion_uptime,
                        "unholy_frenzy_uptime": window.unholy_frenzy_uptime,
                        "berserking_uptime": window.berserking_uptime,
                        "bloodfury_uptime": window.bloodfury_uptime,
                        "fallen_crusader_uptime": window.fallen_crusader_uptime,
                        "start": window.start,
                        "end": window.end,
                        "trinket_uptimes": [
                            {
                                "name": t["trinket"].name,
                                "uptime": t["uptime"].uptime(),
                                "icon": t["trinket"].icon,
                            }
                            for t in window.trinket_uptimes
                        ],
                    }
                    for window in self.windows
                ],
            }
        }


class GargoyleWindow(Window):
    def __init__(
        self,
        start,
        fight_duration,
        buff_tracker: BuffTracker,
        ignore_windows,
        items: ItemPreprocessor,
    ):
        self.start = start
        self.end = min(start + 30000, fight_duration)
        self._gargoyle_first_cast = None
        self.snapshotted_synapse = buff_tracker.is_active("Synapse Springs", start)
        self.snapshotted_fc = buff_tracker.is_active("Unholy Strength", start)
        self.snapshotted_potion = buff_tracker.is_active("Golem's Strength", start)
        self.snapshotted_t11 = (
            buff_tracker.is_active("Death Eater", start) if items.has_t11_4p() else None
        )
        self.snapshotted_bloodfury = buff_tracker.is_active("Blood Fury", start) if buff_tracker.has_bloodfury else None

        self.num_melees = 0
        self.num_casts = 0
        self.total_damage = 0
        self._items = items
        self._snapshottable_trinkets = []
        self._uptime_trinkets = []
        self.trinket_snapshots = []

        for trinket in self._items.trinkets:
            if trinket.snapshots_gargoyle:
                self._snapshottable_trinkets.append(trinket)
            else:
                self._uptime_trinkets.append(trinket)

        for snapshottable_trinket in self._snapshottable_trinkets:
            self.trinket_snapshots.append(
                {
                    "trinket": snapshottable_trinket,
                    "did_snapshot": buff_tracker.is_active(
                        snapshottable_trinket.buff_name, start
                    ),
                }
            )

    def _set_gargoyle_first_cast(self, event):
        self._gargoyle_first_cast = event["timestamp"]

    def add_event(self, event):

        if event["source"] == "Ebon Gargoyle":
            if (
                event["type"] in ("cast", "startcast")
                and self._gargoyle_first_cast is None
            ):
                self._set_gargoyle_first_cast(event)
            if event["type"] == "cast":
                if event["ability"] == "Melee":
                    self.num_melees += 1
                if event["ability"] == "Gargoyle Strike":
                    self.num_casts += 1

        if event["type"] == "damage" and event["source"] == "Ebon Gargoyle":
            self.total_damage += event["amount"]

    def score(self):
        return ScoreWeight.calculate(
            ScoreWeight(int(self.snapshotted_synapse), 2),
            ScoreWeight(int(self.snapshotted_fc), 3),
            ScoreWeight(int(self.snapshotted_potion), 3),
            # Lower weight since this only lasts 12s
            ScoreWeight(self.num_casts / 18, 4),
            ScoreWeight(
                len([t for t in self.trinket_snapshots if t["did_snapshot"]])
                / (len(self.trinket_snapshots) if self.trinket_snapshots else 1),
                len(self.trinket_snapshots) * 2,
            ),
            ScoreWeight(
                int(self.snapshotted_t11) if self.snapshotted_t11 is not None else 0,
                2 if self.snapshotted_t11 is not None else 0,
            ),
            ScoreWeight(
                int(self.snapshotted_bloodfury) if self.snapshotted_bloodfury is not None else 0,
                2 if self.snapshotted_bloodfury is not None else 0,
            ),
        )


class GargoyleAnalyzer(BaseAnalyzer):
    INCLUDE_PET_EVENTS = True

    def __init__(self, fight_duration, buff_tracker, ignore_windows, items):
        self.windows: List[GargoyleWindow] = []
        self._window = None
        self._buff_tracker = buff_tracker
        self._fight_duration = fight_duration
        self._ignore_windows = ignore_windows
        self._items = items

    def add_event(self, event):
        if event["type"] == "cast" and event["ability"] == "Summon Gargoyle":
            self._window = GargoyleWindow(
                event["timestamp"],
                self._fight_duration,
                self._buff_tracker,
                self._ignore_windows,
                self._items,
            )
            self.windows.append(self._window)

        if not self._window:
            return

        self._window.add_event(event)

    @property
    def possible_gargoyles(self):
        return max(1 + (self._fight_duration - 10000) // 183000, len(self.windows))

    def score(self):
        window_score = sum(window.score() for window in self.windows)
        return ScoreWeight.calculate(
            ScoreWeight(
                window_score / self.possible_gargoyles, 5 * self.possible_gargoyles
            ),
        )

    def report(self):
        return {
            "gargoyle": {
                "score": self.score(),
                "num_possible": self.possible_gargoyles,
                "num_actual": len(self.windows),
                "average_damage": (
                    sum(window.total_damage for window in self.windows)
                    / len(self.windows)
                    if self.windows
                    else 0
                ),
                "windows": [
                    {
                        "score": window.score(),
                        "damage": window.total_damage,
                        "snapshotted_synapse": window.snapshotted_synapse,
                        "snapshotted_potion": window.snapshotted_potion,
                        "snapshotted_fc": window.snapshotted_fc,
                        "snapshotted_t11": window.snapshotted_t11,
                        "snapshotted_bloodfury": window.snapshotted_bloodfury,
                        "num_casts": window.num_casts,
                        "num_melees": window.num_melees,
                        "start": window.start,
                        "end": window.end,
                        "trinket_snapshots": [
                            {
                                "name": t["trinket"].name,
                                "did_snapshot": t["did_snapshot"],
                                "icon": t["trinket"].icon,
                            }
                            for t in window.trinket_snapshots
                        ],
                    }
                    for window in self.windows
                ],
            }
        }


class DeathAndDecayUptimeAnalyzer(BaseAnalyzer):
    def __init__(self, fight_duration, ignore_windows, items):
        self._dnd_ticks = 0
        self._last_tick_time = None
        self._ignore_windows = ignore_windows

        ignore_duration = sum(window.duration for window in self._ignore_windows)
        self._fight_duration = fight_duration - ignore_duration

    def _is_in_ignore_window(self, timestamp):
        for window in self._ignore_windows:
            if window.start <= timestamp <= window.end:
                return True
        return False

    def add_event(self, event):
        if event["type"] == "damage" and event["ability"] == "Death and Decay":
            if (
                self._last_tick_time is None
                or event["timestamp"] - self._last_tick_time > 800
            ) and not self._is_in_ignore_window(event["timestamp"]):
                self._dnd_ticks += 1
                self._last_tick_time = event["timestamp"]

    @property
    def max_uptime(self):
        return 13 / 40

    def uptime(self):
        return self._dnd_ticks / (self._fight_duration // 1000)

    def score(self):
        return min(1, self.uptime() / self.max_uptime)

    def report(self):
        return {
            "dnd": {
                "max_uptime": self.max_uptime,
                "uptime": self.uptime(),
            }
        }


class GhoulAnalyzer(BaseAnalyzer):
    INCLUDE_PET_EVENTS = True

    def __init__(self, fight_duration, ignore_windows):
        self._fight_duration = fight_duration
        self._num_claws = 0
        self._num_sweeping_claws = 0
        self._num_gnaws = 0
        self._melee_uptime = MeleeUptimeAnalyzer(
            fight_duration,
            ignore_windows,
            event_predicate=self._is_ghoul,
        )
        self._windows = []
        self._window = None
        self.total_damage = 0
        self._ignore_windows = ignore_windows

    def _is_ghoul(self, event):
        if not event["is_owner_pet_source"] and not event["is_owner_pet_target"]:
            return False

        if event["source"] in ("Army of the Dead", "Ebon Gargoyle") or event[
            "target"
        ] in ("Army of the Dead", "Ebon Gargoyle"):
            return False

        return True

    def add_event(self, event):
        # Should be called at the top so we can update the window
        self._melee_uptime.add_event(event)

        # Ghoul was revived
        if event["type"] == "cast" and event["ability"] == "Raise Dead":
            # It seems this can happen if the ghoul is dismissed
            if self._window and self._window.end is None:
                self._window.end = event["timestamp"]
            self._window = Window(event["timestamp"])
            self._windows.append(self._window)
            return

        if not self._is_ghoul(event):
            return

        # Ghoul was already alive
        if not self._windows:
            self._window = Window(0)
            self._windows.append(self._window)

        if "Ghoul" in event["source"] and event["type"] == "damage":
            if event["ability"] == "Claw":
                self._num_claws += 1
            elif event["ability"] == "Sweeping Claws":
                self._num_sweeping_claws += 1
            elif event["ability"] == "Gnaw":
                self._num_gnaws += 1
            elif event["type"] == "damage":
                self.total_damage += event["amount"]
        elif event["is_owner_pet_target"]:
            # Ghoul has died
            if event["type"] == "damage" and event.get("overkill"):
                self._window.end = event["timestamp"]

    @property
    def melee_uptime(self):
        return self._melee_uptime.uptime()

    def uptime(self):
        if self._windows and self._windows[-1].end is None:
            self._windows[-1].end = self._fight_duration

        return calculate_uptime(
            self._windows,
            self._ignore_windows,
            self._fight_duration,
        )

    def score(self):
        return ScoreWeight.calculate(
            ScoreWeight(self.melee_uptime, 10),
            ScoreWeight(0 if self._num_gnaws else 1, 1),
        )

    def report(self):
        return {
            "ghoul": {
                "score": self.score(),
                "num_claws": self._num_claws,
                "num_sweeping_claws": self._num_sweeping_claws,
                "num_gnaws": self._num_gnaws,
                "melee_uptime": self._melee_uptime.uptime(),
                "uptime": self.uptime(),
                "damage": self.total_damage,
            }
        }
class ArmyAnalyzer(BaseAnalyzer):
    INCLUDE_PET_EVENTS = True

    def __init__(self):
        self.total_damage = 0

    def add_event(self, event):
        if event["type"] == "damage" and event["source"] == "Army of the Dead":
            self.total_damage += event["amount"]

    def report(self):
        return {
            "army": {
                "damage": self.total_damage,
            }
        }

    def score(self):
        if self.total_damage >= 100000:
            return 1
        else:
            return self.total_damage/100000


class UnholyPresenceUptimeAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        fight_duration,
        buff_tracker: BuffTracker,
        ignore_windows,
    ):
        self._buff_tracker = buff_tracker
        self._ignore_windows = ignore_windows
        # Gargoyle windows are modified throughout the fight
        self._fight_duration = fight_duration

    def uptime(self):
        windows = self._buff_tracker.get_windows("Unholy Presence")
        return calculate_uptime(windows, self._ignore_windows, self._fight_duration)

    def score(self):
        return self.uptime()

    def report(self):
        return {
            "unholy_presence_uptime": self.uptime(),
        }


class SnapshottableBuff:
    def __init__(self, buffs, display_name):
        if isinstance(buffs, str):
            buffs = {buffs}

        self.buffs = buffs
        self.display_name = display_name

    def is_active(self, buff_tracker: BuffTracker, timestamp):
        return any(buff_tracker.is_active(buff, timestamp) for buff in self.buffs)

class BloodTapAnalyzer(BaseAnalyzer):
    def __init__(self, fight_end_time):
        self._num_used = 0
        self._max_blood_tap_cooldown = 60000
        self._fight_end_time = fight_end_time

    @property
    def max_usages(self):
        return max(1 + (self._fight_end_time - (self._max_blood_tap_cooldown / 2)) // self._max_blood_tap_cooldown, self._num_used)

    def add_event(self, event):
        self._max_blood_tap_cooldown = event["blood_tap_cooldown"]
        if event["type"] == "cast" and event["ability"] == "Blood Tap":
            self._num_used += 1

    def score(self):
        return self._num_used / self.max_usages

    def report(self):
        return {
            "blood_tap_usages": self._num_used,
            "blood_tap_max_usages": self.max_usages,
        }

class AMSAnalyzer(BaseAnalyzer):
    def __init__(self, fight_end_time):
        self._num_used = 0
        self._ams_cooldown = 60000
        self._fight_end_time = fight_end_time

    @property
    def max_usages(self):
        return max(1 + (self._fight_end_time - 10000) // self._ams_cooldown, self._num_used)

    def add_event(self, event):
        if event["type"] == "cast" and event["ability"] == "Anti-Magic Shield":
            self._num_used += 1

    def score(self):
        return self._num_used / self.max_usages

    def report(self):
        return {
            "ams_usages": self._num_used,
            "ams_max_usages": self.max_usages,
        }


class UnholyAnalysisScorer(AnalysisScorer):
    def get_score_weights(self):
        exponent_factor = 1.5

        return {
            GargoyleAnalyzer: {
                "weight": lambda ga: 3 * ga.possible_gargoyles,
                "exponent_factor": exponent_factor,
            },
            BloodPlagueAnalyzer: {
                "weight": 3,
                "exponent_factor": exponent_factor,
            },
            FrostFeverAnalyzer: {
                "weight": 3,
                "exponent_factor": exponent_factor,
            },
            DarkTransformationUptimeAnalyzer: {
                "weight": 10,
                "exponent_factor": exponent_factor,
                },
            DarkTransformationAnalyzer: {
                "weight": 4,
                "exponent_factor": exponent_factor,
            },
            DeathAndDecayUptimeAnalyzer: {
                "weight": 4,
                "exponent_factor": exponent_factor,
            },
            MeleeUptimeAnalyzer: {
                "weight": 6,
                "exponent_factor": exponent_factor,
            },
            RPAnalyzer: {
                "weight": 1,
            },
            UnholyPresenceUptimeAnalyzer: {
                "weight": 1,
                "exponent_factor": exponent_factor,
            },
            GhoulAnalyzer: {
                "weight": 4,
                "exponent_factor": exponent_factor,
            },
            BuffTracker: {
                "weight": 1,
            },
            BombAnalyzer: {
                "weight": 1,
            },
            SynapseSpringsAnalyzer: {
                "weight": 2,
            },
            TrinketAnalyzer: {
                "weight": lambda ta: ta.num_on_use_trinkets * 2,
            },
            T11UptimeAnalyzer: {
                "weight": lambda t11a: t11a.score_weight(),
            },
            # T12UptimeAnalyzer: {
            #     "weight": lambda t12a: t12a.score_weight(),
            # },
            BloodTapAnalyzer: {
                "weight": 1,
            },
        }

    def report(self):
        return {
            "analysis_scores": {
                "total_score": self.score(),
            }
        }


class UnholyAnalysisConfig(CoreAnalysisConfig):
    def get_analyzers(self, fight: Fight, buff_tracker, dead_zone_analyzer, items):
        dead_zones = dead_zone_analyzer.get_dead_zones()
        gargoyle = GargoyleAnalyzer(fight.duration, buff_tracker, dead_zones, items)
        dark_transformation = DarkTransformationAnalyzer(fight.duration, buff_tracker, dead_zones, items)

        return super().get_analyzers(fight, buff_tracker, dead_zone_analyzer, items) + [
            DarkTransformationUptimeAnalyzer(fight.duration, buff_tracker, dead_zones, items),
            gargoyle,
            dark_transformation,
            BloodPlagueAnalyzer(fight.duration, dead_zones),
            FrostFeverAnalyzer(fight.duration, dead_zones),
            DeathAndDecayUptimeAnalyzer(fight.duration, dead_zones, items),
            GhoulAnalyzer(fight.duration, dead_zones),
            UnholyPresenceUptimeAnalyzer(
                fight.duration, buff_tracker, dead_zones
            ),
            ArmyAnalyzer(),
            BloodTapAnalyzer(fight.end_time),
            # AMSAnalyzer(fight.end_time)
        ]

    def get_scorer(self, analyzers):
        return UnholyAnalysisScorer(analyzers)

    def create_rune_tracker(self):
        return RuneTracker(
            should_convert_blood=True,
            should_convert_frost=True,
            track_drift_type={"Unholy"},
        )
