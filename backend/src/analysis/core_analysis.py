import functools
import itertools
from collections import defaultdict
from typing import Optional

from analysis.base import (
    AnalysisScorer,
    BaseAnalyzer,
    BasePreprocessor,
    Window,
    calculate_uptime,
    range_overlap,
)
from analysis.items import Trinket, ItemPreprocessor
from report import Fight


class DeadZoneAnalyzer(BasePreprocessor):
    MELEE_ABILITIES = {
        "Melee",
        "Obliterate",
        "Frost Strike",
        "Festering Strike",
        "Plague Strike",
        "Scourge Strike",
        "Pestilence",
    }

    class DeadZone(Window):
        def __init__(self, last_timestamp, curr_timestamp):
            super().__init__(last_timestamp + 1, curr_timestamp)

        def __contains__(self, item):
            return self.start <= item <= self.end

    def __init__(self, fight: Fight):
        self._fight = fight
        self._dead_zones = []
        self._last_event = None
        self._last_timestamp = 0
        self._checker = {
            "Ascendant Council": self._check_ascendant_council,
            "Atramedes": functools.partial(
                self._check_boss_events_occur, only_melee=True
            ),
            "Al'Akir": self._check_al_akir,
            "Nefarion's End": self._check_nefarion_mind_control,
            "Loatheb": self._check_loatheb,
            "Thaddius": self._check_thaddius,
            "Maexxna": self._check_maexxna,
            "Kel'Thuzad": self._check_kelthuzad,
            "Ignis the Furnace Master": self._check_ignis,
            "Razorscale": self._check_razorscale,
            "Algalon the Observer": self._check_algalon,
            "The Northrend Beasts": self._check_boss_events_occur,
            "Anub'arak": self._check_boss_events_occur,
        }.get(self._fight.encounter.name)
        self._encounter_name = self._fight.encounter.name
        self._is_hard_mode = self._fight.is_hard_mode

    def _check_boss_events_occur(self, event, only_melee=False):
        if event.get("source_is_boss") or (
            event.get("target_is_boss") and event["type"] == "cast"
        ):
            if only_melee and event["ability"] not in self.MELEE_ABILITIES:
                return

            if event["timestamp"] - self._last_timestamp > 7000:
                dead_zone = self.DeadZone(self._last_timestamp, event["timestamp"])
                self._dead_zones.append(dead_zone)
            self._last_timestamp = event["timestamp"]

    def _check_ascendant_council(self, event):
        if event.get("target") not in (
            "Ignacious",
            "Arion",
            "Terrastra",
            "Feludius",
            "Elementium Monstrosity",
        ):
            return

        if (
            not self._last_event
            and event["type"] == "damage"
            and event["target"] in ("Arion", "Terrastra")
            and "hitPoints" in event
            and event["hitPoints"] / event["maxHitPoints"] <= 0.25
        ):
            self._last_event = event
        if (
            (
                event.get("source") == "Elementium Monstrosity"
                or event.get("target") == "Elementium Monstrosity"
            )
            and self._last_event
            and not self._dead_zones
        ):
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

    def _check_al_akir(self, event):
        if event.get("target") != "Al'Akir":
            return
        if (
            not self._last_event
            and event["type"] == "damage"
            and event["target"] == "Al'Akir"
            and "hitPoints" in event
            and event["hitPoints"] / event["maxHitPoints"] <= 0.25
        ):
            self._last_event = event
        if (
            self._last_event
            and not self._dead_zones
            and event["timestamp"] - self._last_event["timestamp"] > 5000
        ):
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

    def _check_nefarion_mind_control(self, event):
        if event["ability"] not in ("Free Your Mind", "Siphon Power"):
            return

        if not self._last_event and event["ability"] == "Siphon Power":
            self._last_event = event
        if event["ability"] == "Free Your Mind" and self._last_event:
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)
            self._last_event = None

    def _check_algalon(self, event):
        if event["type"] not in ("applydebuff", "removedebuff"):
            return

        if event["ability"] != "Black Hole":
            return

        if event["type"] == "applydebuff":
            self._last_event = event
        elif event["type"] == "removedebuff":
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

    def _check_ignis(self, event):
        if event["type"] not in ("removedebuff", "applydebuff"):
            return

        if event["ability"] != "Slag Pot":
            return

        if event["type"] == "applydebuff":
            self._last_event = event
        elif event["type"] == "removedebuff":
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

    def _check_kelthuzad(self, event):
        if event["type"] not in ("removedebuff", "applydebuff"):
            return

        if event["ability"] != "Frost Blast":
            return

        if event["type"] == "applydebuff":
            self._last_event = event
        elif event["type"] == "removedebuff":
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

    def _check_maexxna(self, event):
        if event["type"] not in ("removedebuff", "applydebuff"):
            return

        if event["ability"] != "Web Spray":
            return

        if event["type"] == "applydebuff":
            self._last_event = event
        elif event["type"] == "removedebuff":
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

    def _check_thaddius(self, event):
        if event["type"] not in ("cast", "damage"):
            return

        if event.get("target") not in ("Thaddius", "Stalagg", "Feugen"):
            return

        if event["source"] != self._fight.source.name:
            return

        if self._last_event and self._last_event["target"] != event["target"]:
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

        self._last_event = event

    def _check_razorscale(self, event):
        if event.get("target") != "Razorscale":
            return

        if event["type"] != "cast":
            return

        if event["source"] != self._fight.source.name:
            return

        if (
            self._last_event
            and event["timestamp"] - self._last_event["timestamp"] > 20000
        ):
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

        self._last_event = event

    def _check_loatheb(self, event):
        if event.get("target") != "Loatheb":
            return

        if event["type"] != "cast" or event["ability"] not in self.MELEE_ABILITIES:
            return

        if event["source"] != self._fight.source.name:
            return

        if (
            self._last_event
            and event["timestamp"] - self._last_event["timestamp"] > 2000
        ):
            dead_zone = self.DeadZone(self._last_event["timestamp"], event["timestamp"])
            self._dead_zones.append(dead_zone)

        self._last_event = event

    def preprocess_event(self, event):
        if not self._checker:
            return

        return self._checker(event)

    def get_recent_dead_zone(self, end) -> Optional[DeadZone]:
        for dead_zone in reversed(self._dead_zones):
            # returns the closest dead-zone
            if dead_zone.start <= end:
                return dead_zone
        return None

    def get_dead_zones(self):
        return [
            Window(window.start, min(window.end, self._fight.duration))
            for window in self._dead_zones
            if window.start <= self._fight.duration
        ]

    def decorate_event(self, event):
        dead_zone = self.get_recent_dead_zone(event["timestamp"])
        event["in_dead_zone"] = dead_zone and event["timestamp"] in dead_zone
        event["recent_dead_zone"] = dead_zone and (dead_zone.start, dead_zone.end)


class Rune:
    def __init__(self, full_name, type):
        self.full_name = full_name
        self.type = type
        self.regen_time = 0
        # Flag for death rune (when converted normally)
        self.is_death = False
        # Blood Tap is tracked as separate attribute since a blood-tapped
        # death rune doesn't convert back to blood when used
        # like a normal death rune does
        self.blood_tapped = False
        self._regen_speed = 1
        self.rune_cd = 10000
        self._linked_rune = None

    def can_spend(self, timestamp: int):
        return timestamp >= self.regen_time

    def can_spend_death(self, timestamp: int):
        return (self.is_death or self.blood_tapped) and self.can_spend(timestamp)

    def refresh(self, timestamp):
        diff = self.regen_time - timestamp
        if not self._linked_rune.can_spend(timestamp):
            # remove the diff from the linked rune
            self._linked_rune.regen_time -= diff

        self.regen_time = timestamp

    def spend(self, timestamp: int, convert: bool):
        if not self.can_spend(timestamp):
            return False, 0

        self.regen_time = timestamp + self.rune_cd

        if not self._linked_rune.can_spend(timestamp):
            # calculate how long until the linked rune is available
            time_until_linked_rune = self._linked_rune.regen_time - timestamp
            # add the time to this rune
            self.regen_time = self.regen_time + time_until_linked_rune

        if convert and not self.blood_tapped:
            self.convert_to_death()
        return True

    def convert_to_death(self):
        assert not self.blood_tapped
        self.is_death = True

    def blood_tap(self):
        assert not self.is_death
        self.blood_tapped = True

    def stop_blood_tap(self):
        self.blood_tapped = False

    def spend_death(self, timestamp: int, convert_back: bool):
        if not self.can_spend_death(timestamp):
            return False, 0

        spend = self.spend(timestamp, False)
        if not spend:
            return spend

        if convert_back and not self.blood_tapped:
            self.is_death = False
        return spend

    def get_name(self):
        if self.is_death or self.blood_tapped:
            return "Death"
        return self.type

    def time_since_regen(self, timestamp):
        if self.regen_time == 0:
            return 0
        return max(0, timestamp - self.regen_time)

    def set_regen_speed(self, timestamp, speed):
        current_speed = self._regen_speed
        self._regen_speed = speed
        self.rune_cd = 10000 * speed

        if current_speed != speed and self.regen_time > timestamp:
            self.regen_time = (
                timestamp + (self.regen_time - timestamp) * speed / current_speed
            )

    def set_linked_rune(self, rune):
        self._linked_rune = rune


class RuneHasteTracker(BaseAnalyzer):
    HASTE_RATING_PROCS = {
        # Shrine-Cleansing Purifier
        91355: 1314,
        # Crushing Weight
        91821: 1926,
        # Crushing Weight (H)
        92342: 2178,
    }
    HASTE_PERCENT_PROCS = {
        "Unholy Frenzy": 1.2,
        "Runic Corruption": 2,
        "Bloodlust": 1.3,
        "Heroism": 1.3,
        "Time Warp": 1.3,
        "Primal Rage": 1.3,
        "Unholy Presence": 1.15,
        "Berserking": 1.2,
    }

    def __init__(self, combatant_info, buff_tracker, rune_tracker):
        self._initial_haste_rating = combatant_info["hasteMelee"]
        self._current_haste_rating = combatant_info["hasteMelee"]
        self._current_haste_percent = 1.0
        self._rune_tracker = rune_tracker

        for haste_percent_proc in self.HASTE_PERCENT_PROCS:
            if buff_tracker.has_buff(haste_percent_proc):
                self._current_haste_percent *= self.HASTE_PERCENT_PROCS[
                    haste_percent_proc
                ]

        self._modify_haste(
            0,
            self._current_haste_rating,
            self._current_haste_percent,
        )

    def add_event(self, event):
        new_haste_rating = self._current_haste_rating
        if (
            event["type"] == "applybuff"
            and event["abilityGameID"] in self.HASTE_RATING_PROCS
        ):
            new_haste_rating += self.HASTE_RATING_PROCS[event["abilityGameID"]]
        if (
            event["type"] == "removebuff"
            and event["abilityGameID"] in self.HASTE_RATING_PROCS
        ):
            new_haste_rating -= self.HASTE_RATING_PROCS[event["abilityGameID"]]

        new_haste_percent = self._current_haste_percent
        if (
            event["type"] == "applybuff"
            and event["ability"] in self.HASTE_PERCENT_PROCS
        ):
            new_haste_percent *= self.HASTE_PERCENT_PROCS[event["ability"]]
        if (
            event["type"] == "removebuff"
            and event["ability"] in self.HASTE_PERCENT_PROCS
        ):
            new_haste_percent /= self.HASTE_PERCENT_PROCS[event["ability"]]

        if (
            new_haste_rating != self._current_haste_rating
            or new_haste_percent != self._current_haste_percent
        ):
            self._modify_haste(event["timestamp"], new_haste_rating, new_haste_percent)

    def _modify_haste(self, timestamp, haste_rating, haste_percent):
        self._current_haste_rating = haste_rating
        self._current_haste_percent = haste_percent

        haste_from_rating = 1 + haste_rating / 12805.7160
        haste = haste_from_rating * haste_percent
        rune_speed = 1 / haste

        self._rune_tracker.update_regen_speed(timestamp, rune_speed)


class RuneTracker(BaseAnalyzer):
    def __init__(self, should_convert_blood, should_convert_frost):
        self.runes = [
            Rune("Blood1", "Blood"),
            Rune("Blood2", "Blood"),
            Rune("Frost1", "Frost"),
            Rune("Frost2", "Frost"),
            Rune("Unholy1", "Unholy"),
            Rune("Unholy2", "Unholy"),
        ]
        for i in range(0, 6, 2):
            first, second = self.runes[i], self.runes[i + 1]
            first.set_linked_rune(second)
            second.set_linked_rune(first)

        self.rune_spend_error = False
        self._should_convert_blood = should_convert_blood
        self._should_convert_frost = should_convert_frost

    @property
    def current_death_runes(self):
        return [r for r in self.runes if r.is_death or r.blood_tapped]

    def _sorted_runes(self, runes):
        runes_ = [(rune, i) for i, rune in enumerate(runes)]
        runes_sorted = sorted(runes_, key=lambda r: (r[0].regen_time or 0, r[1]))
        return [rune for rune, _ in runes_sorted]

    def resync_runes(self, timestamp, rune_cost, runes_used):
        def _resync_runes(runes, num):
            refreshed = 0

            for rune in self._sorted_runes(runes):
                if refreshed >= num:
                    break
                if not rune.can_spend(timestamp):
                    rune.refresh(timestamp)
                    refreshed += 1

            return refreshed == num

        total_cost = rune_cost["Blood"] + rune_cost["Frost"] + rune_cost["Unholy"]
        total_used = runes_used["Blood"] + runes_used["Frost"] + runes_used["Unholy"]

        _resync_runes(self.runes[0:2], runes_used["Blood"])
        _resync_runes(self.runes[2:4], runes_used["Frost"])
        _resync_runes(self.runes[4:6], runes_used["Unholy"])
        _resync_runes(self.current_death_runes, total_cost - total_used)

    def _spend_runes(self, num, runes, timestamp, death_rune_slots, convert=False):
        if not num:
            return True

        spent = 0

        for rune in runes:
            if spent == num:
                break
            # Don't spend deaths here in order to prioritize normal runes,
            # deaths will be done in next loop
            if rune.can_spend(timestamp) and not rune.can_spend_death(timestamp):
                rune.spend(timestamp, convert)
                spent += 1

        for rune in death_rune_slots:
            if spent == num:
                break
            if rune.can_spend_death(timestamp):
                rune.spend_death(timestamp, convert_back=not convert)
                spent += 1

                # This handles the case where we use a death rune for a spell
                # that would convert some runes to death.
                # The in-game behaviour is that if a death is used instead,
                # then it finds a rune that could have been converted and does so
                if convert and rune.blood_tapped:
                    # A rune should never be both blood tapped and a
                    # normally converted death rune
                    assert not rune.is_death

                    # Find the first non-blood-tapped rune and convert it
                    for rune_ in runes:
                        if not rune_.is_death and not rune_.blood_tapped:
                            rune_.convert_to_death()
                            break

        return spent == num

    def spend(self, ability, timestamp: int, blood: int, frost: int, unholy: int):
        convert_blood = self._should_convert_blood and ability in (
            "Festering Strike",
            "Pestilence",
            "Blood Strike",
        )
        convert_frost = self._should_convert_frost and ability in ("Festering Strike",)
        blood_spend = self._spend_runes(
            blood,
            self.runes[0:2],
            timestamp,
            death_rune_slots=self.runes[:4],
            convert=convert_blood,
        )
        frost_spend = self._spend_runes(
            frost,
            self.runes[2:4],
            timestamp,
            # prioritize frost-converted death runes before blood ones
            death_rune_slots=itertools.chain(self.runes[2:4], self.runes[:2]),
            convert=convert_frost,
        )
        unholy_spend = self._spend_runes(
            unholy,
            self.runes[4:6],
            timestamp,
            death_rune_slots=self.runes[:4],
        )

        spent = all([blood_spend, frost_spend, unholy_spend])
        return spent

    def blood_tap(self, timestamp: int):
        # Convert one of the runes to a death rune
        for i in range(2):
            if not self.runes[i].is_death:
                self.runes[i].blood_tap()
                break

        # Refresh the cooldown of one of the runes
        for i in range(2):
            if not self.runes[i].can_spend(timestamp):
                self.runes[i].refresh(timestamp)
                break

    def stop_blood_tap(self):
        for i in range(2):
            if self.runes[i].blood_tapped:
                self.runes[i].stop_blood_tap()
                break

    def erw(self, timestamp: int):
        for i in range(6):
            if not self.runes[i].can_spend(timestamp):
                self.runes[i].refresh(timestamp)

    def current_runes(self, timestamp):
        def _count_rune(i):
            return (
                1
                if self.runes[i].can_spend(timestamp)
                and not (self.runes[i].is_death or self.runes[i].blood_tapped)
                else 0
            )

        return {
            "Blood": sum(_count_rune(i) for i in range(0, 2)),
            "Frost": sum(_count_rune(i) for i in range(2, 4)),
            "Unholy": sum(_count_rune(i) for i in range(4, 6)),
            "Death": sum(
                1 for rune in self.current_death_runes if rune.can_spend(timestamp)
            ),
        }

    def add_event(self, event):
        if event.get("rune_cost"):
            runes_needed = defaultdict(int)
            current_runes = self.current_runes(event["timestamp"])
            death_runes = current_runes["Death"]

            total_missing = 0
            for rune_type, num_needed in event["rune_cost"].items():
                missing = max(0, num_needed - current_runes[rune_type])
                if missing > 0:
                    death_runes_needed = min(death_runes, missing)
                    missing -= death_runes_needed
                    death_runes -= death_runes_needed
                total_missing += missing

                # respawn the oldest rune if we need it
                for rune in self._sorted_runes(self.runes):
                    if (
                        missing > 0
                        and not rune.can_spend(event["timestamp"])
                        and (rune.type == rune_type or rune.is_death)
                    ):
                        missing -= 1
                        runes_needed[rune_type] += 1

            if total_missing > 0:
                # Sync runes to what we think they should be
                self.resync_runes(event["timestamp"], event["rune_cost"], runes_needed)
                event["rune_spend_adjustment"] = True

        event["runes_before"] = self._serialize(event["timestamp"])

        if event["type"] == "cast":
            if event.get("rune_cost"):
                spent = self.spend(
                    event["ability"],
                    event["timestamp"],
                    blood=event["rune_cost"]["Blood"],
                    frost=event["rune_cost"]["Frost"],
                    unholy=event["rune_cost"]["Unholy"],
                )
                event["rune_spend_error"] = not spent

            if event["ability"] == "Blood Tap":
                self.blood_tap(event["timestamp"])

            if event["ability"] == "Empower Rune Weapon":
                self.erw(event["timestamp"])

        if event["type"] == "removebuff" and event["ability"] == "Blood Tap":
            self.stop_blood_tap()

        event["runes"] = self._serialize(event["timestamp"])

    def update_regen_speed(self, timestamp, rune_speed):
        """
        1. identify rune that will come off CD first
        2. update rune regen time based on new speed
        3. update linked rune regen time based on new speed and time until first rune is available
        """
        for i in range(0, 6, 2):
            rune_a, rune_b = self.runes[i], self.runes[i + 1]

            # "first" is the rune that will come off CD first
            if rune_a.regen_time < rune_b.regen_time:
                first, second = rune_a, rune_b
            else:
                first, second = rune_b, rune_a

            # remove the current "wait time"
            if first.regen_time > timestamp:
                second.regen_time -= first.rune_cd

            first.set_regen_speed(timestamp, rune_speed)
            second.set_regen_speed(timestamp, rune_speed)

            # add the new "wait time" until the second rune can start regen
            if first.regen_time > timestamp:
                second.regen_time += first.rune_cd

    def _serialize(self, timestamp):
        return [
            {
                "name": rune.get_name(),
                "is_available": rune.can_spend(timestamp),
                "regen_time": rune.regen_time,
            }
            for rune in self.runes
        ]


class PrepullArmyOfTheDeadTracker(BasePreprocessor):
    # Ghouls last 40 seconds after they are target-able, assume 500ms to target
    ARMY_DURATION_MS = 40500
    ARMY_CAST_TIME_MS = 4000

    def __init__(self, rune_tracker: RuneTracker):
        self._rune_tracker = rune_tracker
        self._deaths = {}
        self._runes_modified = False

    def preprocess_event(self, event):
        if self._runes_modified or event["timestamp"] > self.ARMY_DURATION_MS:
            return

        if event.get("source") == "Army of the Dead":
            self._deaths[event["sourceInstance"]] = event["source_dies_at"]

        if len(self._deaths) == 8:
            self._modify_runes()

    def _modify_runes(self):
        # get the max death time
        max_death_time = max(self._deaths.values())
        cast_at = max_death_time - self.ARMY_DURATION_MS - self.ARMY_CAST_TIME_MS
        rune_cd = self._rune_tracker.runes[0].rune_cd

        for i in range(0, 6, 2):
            self._rune_tracker.runes[i].regen_time = cast_at + rune_cd

        self._runes_modified = True


class BuffWindows:
    def __init__(self, buff_name, buff_id, icon):
        self.buff_name = buff_name
        self.buff_id = buff_id
        self.icon = icon
        self._windows = []

    @property
    def has_window(self):
        return len(self._windows) > 0

    @property
    def has_active_window(self):
        return self.has_window and self._windows[-1].end is None

    @property
    def active_window(self):
        if not self.has_window:
            return None
        return self._windows[-1]

    @property
    def windows(self):
        return self._windows

    @property
    def num_windows(self):
        return len(self._windows)

    def pop(self):
        return self._windows.pop()

    def add_window(self, start, end=None):
        self._windows.append(Window(start, end))

    def contains(self, timestamp):
        for window in self._windows:
            if window.contains(timestamp):
                return True
        return False

    def containing_window(self, timestamp):
        for window in self._windows:
            if window.contains(timestamp):
                return window
        return None


class BuffTracker(BaseAnalyzer, BasePreprocessor):
    def __init__(self, buffs_to_track, end_time, starting_auras, spec):
        self._buffs_to_track = buffs_to_track
        self._spec = spec
        self._end_time = end_time
        self._buff_windows = {}
        self._add_starting_auras(starting_auras)
        self._presences = {"Blood Presence", "Frost Presence", "Unholy Presence"}

    def _get_buff_windows(self, buff_name, buff_id, icon):
        return self._buff_windows.setdefault(
            buff_name,
            BuffWindows(buff_name, buff_id, icon),
        )

    def _num_windows(self, buff_name):
        if buff_name not in self._buff_windows:
            return 0
        return self._buff_windows[buff_name].num_windows

    def get_windows(self, buff_name):
        if buff_name not in self._buff_windows:
            return []

        windows = self._buff_windows[buff_name].windows
        if windows and windows[-1].end is None:
            windows[-1] = Window(windows[-1].start, self._end_time)
        return windows

    @property
    def has_flask(self):
        # WCL is not reporting this accurate so for the sake of argument, setting to true
        return True
        # return bool(self._num_windows("Flask of Titanic Strength")) or bool(self._num_windows("Flask of Battle"))

    @property
    def num_pots(self):
        return self._num_windows("Golem's Strength")

    @property
    def has_bl(self):
        return (
            bool(self._num_windows("Bloodlust"))
            or bool(self._num_windows("Heroism"))
            or bool(self._num_windows("Time Warp"))
        )

    @property
    def has_crushing_weight(self):
        return bool(self._num_windows("Race Against Death"))

    @property
    def has_potion(self):
        return bool(self._num_windows("Golem's Strength"))

    @property
    def has_fatality(self):
        return bool(self._num_windows("Fatality"))

    @property
    def has_unholy_frenzy(self):
        return bool(self._num_windows("Unholy Frenzy"))

    @property
    def has_synapse_springs(self):
        return bool(self._num_windows("Synapse Springs"))

    @property
    def has_berserking(self):
        return bool(self._num_windows("Berserking"))

    @property
    def has_fallen_crusader(self):
        return bool(self._num_windows("Unholy Strength"))

    @property
    def has_bloodfury(self):
        return bool(self._num_windows("Blood Fury"))

    def has_buff(self, buff_name):
        if buff_name not in self._buff_windows:
            return False
        return self._buff_windows[buff_name].has_active_window

    def preprocess_event(self, event):
        if event["type"] not in (
            "applybuff",
            "removebuff",
            "removebuffstack",
            "refreshbuff",
            "heal",
        ):
            return

        windows = self._get_buff_windows(
            event["ability"],
            event["abilityGameID"],
            event["ability_icon"],
        )

        if event["type"] in ("removebuffstack", "refreshbuff", "heal"):
            # If we don't have a window, assume it was a starting aura
            if not windows.has_window:
                # resolve the issue where combatant info lags behind the first event
                # ie. on beasts when army is snapshotted with UP
                if event["ability"] in self._presences:
                    for presence in self._presences:
                        presence_windows = self._buff_windows.get(presence)
                        if presence_windows and presence_windows.has_active_window:
                            presence_windows.pop()
                windows.add_window(0)
        elif event["type"] == "applybuff":
            if event["ability"] in ("Golem's Strength"):
                if self.is_active("Golem's Strength", event["timestamp"]):
                    self._buff_windows["Golem's Strength"].pop()

            if not windows.has_active_window:
                windows.add_window(event["timestamp"])
        elif event["type"] == "removebuff":
            end = event["timestamp"]
            if windows.has_active_window:
                windows.active_window.end = end
            elif not windows.has_window:  # assume it was a starting aura
                windows.add_window(0, end)

    def _add_starting_auras(self, starting_auras):
        for aura in starting_auras:
            if "name" in aura:
                windows = self._get_buff_windows(
                    aura["name"],
                    aura["ability"],
                    aura["ability_icon"],
                )
                # Unholy presence can be there twice somehow
                if not windows.has_window:
                    windows.add_window(0)

    def score(self):
        if self._spec == "Frost":
            total_pots = max(2, self.num_pots)
            pot_score = self.num_pots / total_pots * 0.5
            # potentially need to fix flasks
            # flask_score = 0.5 if self.has_flask else 0
            return pot_score
            # return pot_score + flask_score
        return int(self.has_flask)

    def report(self):
        ret = {
            "flask_usage": {
                "has_flask": self.has_flask,
            },
            "potions_used": self.num_pots,
        }
        ret["potion_usage"] = {
            "potions_used": self.num_pots,
        }
        return ret

    def is_active(self, buff, timestamp):
        if buff not in self._buff_windows:
            return False
        return self._buff_windows[buff].contains(timestamp)

    def get_active_buffs(self, timestamp):
        windows = []

        for buff, buff_windows in self._buff_windows.items():
            if buff in self._buffs_to_track:
                containing_window = buff_windows.containing_window(timestamp)

                if containing_window:
                    windows.append(
                        {
                            "ability": buff,
                            "ability_icon": buff_windows.icon,
                            "abilityGameID": buff_windows.buff_id,
                            "start": containing_window.start,
                        }
                    )
        return sorted(
            windows, key=lambda x: ("Presence" not in x["ability"], x["start"])
        )

    def decorate_event(self, event):
        event["buffs"] = self.get_active_buffs(event["timestamp"])

        if event.get("ability") in self._presences:
            # only keep the first presence
            presences = [
                buff for buff in event["buffs"] if "Presence" in buff["ability"]
            ][1:]
            event["buffs"] = [buff for buff in event["buffs"] if buff not in presences]


class PetNameDetector(BasePreprocessor):
    INCLUDE_PET_EVENTS = True

    def __init__(self):
        self._pet_names = {}

    def preprocess_event(self, event):
        if event["source"] in ("Army of the Dead", "Ghoul", "Ebon Gargoyle"):
            return

        if event.get("ability") == "Gargoyle Strike":
            self._pet_names[event["sourceID"]] = "Ebon Gargoyle"
        if event.get("ability") == "Claw":
            if event.get("sourceInstance", 0) > 0:
                self._pet_names[event["sourceID"]] = "Army of the Dead"
            else:
                self._pet_names[event["sourceID"]] = "Ghoul"

    def decorate_event(self, event):
        if event.get("sourceID") in self._pet_names:
            event["source"] = self._pet_names[event["sourceID"]]


class RPAnalyzer(BaseAnalyzer):
    def __init__(self):
        self._count_wasted = 0
        self._sum_wasted = 0
        self._count_gained = 0
        self._sum_gained = 0

    def add_event(self, event):
        if event["type"] == "cast" and event.get("runic_power_waste", 0) > 0:
            self._count_wasted += 1
            self._sum_wasted += event["runic_power_waste"] // 10
        if event["type"] == "resourcechange" and "runic_power_gained_ams" in event:
            self._count_gained += 1
            self._sum_gained += event["runic_power_gained_ams"] // 10

    def score(self):
        waste = self._sum_wasted - self._sum_gained
        if waste < 50:
            return 1
        if waste < 100:
            return 0.5
        if waste < 150:
            return 0.25
        return 0

    def report(self):
        return {
            "runic_power": {
                "overcap_times": self._count_wasted,
                "overcap_sum": self._sum_wasted,
                "gained_times": self._count_gained,
                "gained_sum": self._sum_gained,
            }
        }


class GCDAnalyzer(BaseAnalyzer):
    NO_GCD = {
        "Pillar of Frost",
        "Blood Tap",
        "Global Thermal Sapper Charge",
        "Saronite Bomb",
        "Golem's Strength",
        "Empower Rune Weapon",
        "Cobalt Frag Bomb",
        "Synapse Springs",
        "Blood Fury",
        "Berserking",
        "Melee",
        "Path of Illidan",
        "Anti-Magic Shell",
        "Unholy Frenzy",
        "Mind Freeze",
        "Thrill of Victory",
        "Typhoon",
        "Polarization",
        "King of Boars",
        "Forged Fury",
        "Battle Prowess",
        "Blood Presence",
        "Frost Presence",
        "Unholy Presence",
    }

    def __init__(self, source_id, buff_tracker: BuffTracker):
        self._gcds = []
        self._last_event = None
        self._source_id = source_id
        self._buff_tracker = buff_tracker

    def add_event(self, event):
        if not event["type"] == "cast":
            return

        if event["sourceID"] != self._source_id:
            return

        if self._last_event is None:
            offset = event["timestamp"]
            last_timestamp = 0
        else:
            if event["recent_dead_zone"]:
                if event["in_dead_zone"]:
                    last_timestamp = event["timestamp"]
                else:
                    last_timestamp = max(
                        event["recent_dead_zone"][1], self._last_event["timestamp"]
                    )
            else:
                last_timestamp = self._last_event["timestamp"]

            offset = event["timestamp"] - last_timestamp

        event["gcd_offset"] = offset
        event["has_gcd"] = event["ability"] not in self.NO_GCD

        if event["has_gcd"]:
            self._gcds.append((event["timestamp"], last_timestamp))
            self._last_event = event

    @property
    def latencies(self):
        latencies = []

        for timestamp, last_timestamp in self._gcds:
            timestamp_diff = timestamp - last_timestamp
            assumed_gcd = (
                1000
                if self._buff_tracker.is_active("Unholy Presence", timestamp)
                else 1500
            )

            # don't handle spell GCD for now
            latency = timestamp_diff - assumed_gcd
            if latency > -50:
                latencies.append(max(0, latency))

        return latencies

    @property
    def average_latency(self):
        latencies = self.latencies
        # Don't count first GCD
        return sum(latencies[1:]) / len(latencies[1:]) if len(latencies) > 1 else 0

    def score(self):
        return max(0, 1 - 0.0017 * self.average_latency)

    def report(self):
        average_latency = self.average_latency

        return {
            "gcd_latency": {
                "average_latency": average_latency,
            }
        }


class DiseaseAnalyzer(BaseAnalyzer):
    DISEASE_DURATION_MS = 33000

    def __init__(self, encounter_name, fight_end_time):
        self._dropped_diseases_timestamp = []
        self._encounter_name = encounter_name
        self._fight_end_time = fight_end_time

    def add_event(self, event):
        if (
            event["type"] == "removedebuff"
            and event["ability"]
            in (
                "Blood Plague",
                "Frost Fever",
            )
            and event["target_is_boss"]
            and (self._encounter_name != "Thaddius" or not event["in_dead_zone"])
        ):
            if not event["target_dies_at"] or (
                event["target_dies_at"] - event["timestamp"] > 10000
            ):
                self._dropped_diseases_timestamp.append(event["timestamp"])

    @property
    def num_diseases_dropped(self):
        num_diseases_dropped = 0
        last_timestamp = None

        for timestamp in self._dropped_diseases_timestamp:
            # Dropping them at the end of the fight is fine
            if self._fight_end_time - timestamp < 10000:
                continue
            if last_timestamp is None:
                num_diseases_dropped += 1
            elif timestamp - last_timestamp > self.DISEASE_DURATION_MS:
                num_diseases_dropped += 1
            last_timestamp = timestamp
        return num_diseases_dropped

    def score(self):
        if self.num_diseases_dropped == 0:
            return 1
        if self.num_diseases_dropped == 1:
            return 0.5
        return 0

    def report(self):
        return {
            "diseases_dropped": {
                "num_diseases_dropped": self.num_diseases_dropped,
            }
        }


class TalentPreprocessor(BasePreprocessor):
    def __init__(self, combatant_info):
        self._combatant_info = combatant_info
        self._blood_tap_cooldown = 60000
        self._disease_duration = 21000

    def preprocess_event(self, event):
        self.blood_tap_cooldown()
        self.disease_duration()

    def blood_tap_cooldown(self):
        _talents = self._combatant_info.get("talents")
        if _talents[0]["id"] == 6:
            self._blood_tap_cooldown = 45000
        elif _talents[0]["id"] == 7:
            self._blood_tap_cooldown = 30000
        else:
            self._blood_tap_cooldown = 60000

    def disease_duration(self):
        # Need to add calc for masterfrost eventually
        # and add link for frost
        _talents = self._combatant_info.get("talents")
        if _talents[2]["id"] >= 11:
            self._disease_duration = 33000

    def decorate_event(self, event):
        event["blood_tap_cooldown"] = self._blood_tap_cooldown
        event["disease_duration"] = self._disease_duration


class BombAnalyzer(BaseAnalyzer):
    def __init__(self, fight_duration):
        self._fight_duration = fight_duration
        self._num_thermals = 0
        self._num_saronites = 0
        self._num_big_daddys = 0
        self._num_explosive_bolts = 0

    def add_event(self, event):
        if event["type"] != "cast":
            return

        if event["ability"] == "Global Thermal Sapper Charge":
            self._num_thermals += 1

        if event["ability"] == "Saronite Bomb":
            self._num_saronites += 1

        if event["ability"] == "Big Daddy":
            self._num_big_daddys += 1

        if event["ability"] == "Explosive Bolts":
            self._num_explosive_bolts += 1

    @property
    def possible_thermals(self):
        return max(1 + self._fight_duration // 305000, self._num_thermals)

    @property
    def possible_saronites(self):
        return max(
            1 + self._fight_duration // 65000 - self.possible_thermals,
            self._num_saronites,
        )

    def score(self):
        score_thermal = (
            self._num_thermals / self.possible_thermals if self.possible_thermals else 1
        )
        score_saronite = (
            self._num_saronites / self.possible_saronites
            if self.possible_saronites
            else 1
        )
        # Thermal does more than 2x saronite
        return score_thermal * 0.6 + score_saronite * 0.4

    def report(self):
        return {
            "bomb_usage": {
                "thermal_possible": self.possible_thermals,
                "thermal_actual": self._num_thermals,
                "saronite_possible": self.possible_saronites,
                "saronite_actual": self._num_saronites,
            }
        }


class SynapseSpringsAnalyzer(BaseAnalyzer):
    def __init__(self, fight_duration):
        self._fight_duration = fight_duration
        self._num_synapse_springs = 0

    def add_event(self, event):
        if event["type"] == "cast" and event["ability"] == "Synapse Springs":
            self._num_synapse_springs += 1

    @property
    def possible_synapse_springs(self):
        return max(
            1 + (self._fight_duration - 5000) // 63000, self._num_synapse_springs
        )

    def score(self):
        return (
            self._num_synapse_springs / self.possible_synapse_springs
            if self.possible_synapse_springs
            else 1
        )

    def report(self):
        return {
            "synapse_springs": {
                "num_possible": self.possible_synapse_springs,
                "num_actual": self._num_synapse_springs,
            }
        }


class CoreAbilities(BaseAnalyzer):
    CORE_ABILITIES = {
        "Icy Touch",
        "Plague Strike",
        "Pillar of Frost",
        "Obliterate",
        "Pestilence",
        "Howling Blast",
        "Scourge Strike",
        "Festering Strike",
        "Dark Transformation",
        "Death Coil",
        "Frost Strike",
        "Death and Decay",
    }

    def add_event(self, event):
        if event["type"] == "cast":
            if event["ability"] in self.CORE_ABILITIES:
                event["is_core_cast"] = True
            else:
                event["is_core_cast"] = False


class MeleeUptimeAnalyzer(BaseAnalyzer):
    def __init__(
        self, fight_duration, ignore_windows, max_swing_speed=3800, event_predicate=None
    ):
        self._fight_duration = fight_duration
        self._windows = []
        self._window = None
        self._last_swing_at = None
        self._max_swing_speed = max_swing_speed
        self._event_predicate = event_predicate
        self._ignore_windows = ignore_windows

    def predicate(self, event):
        if self._event_predicate is None:
            return True
        return self._event_predicate(event)

    def add_event(self, event):
        if self._window and self._window.end is None:
            if event["timestamp"] - self._last_swing_at >= self._max_swing_speed:
                self._window.end = min(
                    self._last_swing_at + self._max_swing_speed / 2,
                    self._fight_duration,
                )

        if (
            self.predicate(event)
            and event["type"] == "cast"
            and event["ability"] == "Melee"
        ):
            if self._window is None or self._window.end is not None:
                self._window = Window(event["timestamp"])
                self._windows.append(self._window)
            self._last_swing_at = event["timestamp"]

    def uptime(self):
        if self._windows and self._windows[-1].end is None:
            self._windows[-1].end = self._fight_duration

        return calculate_uptime(
            self._windows,
            self._ignore_windows,
            self._fight_duration,
        )

    def score(self):
        return self.uptime()

    def report(self):
        return {
            "melee_uptime": self.uptime(),
        }


class TrinketAnalyzer(BaseAnalyzer):
    def __init__(self, fight_duration, items: ItemPreprocessor):
        self._fight_duration = fight_duration
        self._items = items
        self._trinket_usages = defaultdict(int)

    def _calculate_num_possible(self, trinket: Trinket):
        return max(
            1 + (self._fight_duration - 10000) // (trinket.proc_cd + 3000),
            self._trinket_usages[trinket.buff_name],
        )

    def add_event(self, event):
        if event["type"] == "applybuff" and self._items.has_trinket(event["ability"]):
            self._trinket_usages[event["ability"]] += 1

    def report(self):
        return {
            "trinket_usages": [
                {
                    "name": trinket.name,
                    "num_actual": self._trinket_usages[trinket.buff_name],
                    "num_possible": self._calculate_num_possible(trinket),
                    "icon": trinket.icon,
                }
                for trinket in self._items.trinkets
                if trinket.on_use
            ]
        }

    @property
    def num_on_use_trinkets(self):
        return len([trinket for trinket in self._items.trinkets if trinket.on_use])

    def score(self):
        if self.num_on_use_trinkets == 0:
            return 1

        return (
            sum(
                self._trinket_usages[trinket.buff_name]
                / self._calculate_num_possible(trinket)
                for trinket in self._items.trinkets
                if trinket.on_use
            )
            / self.num_on_use_trinkets
        )


class BuffUptimeAnalyzer(BaseAnalyzer):
    def __init__(
        self,
        end_time,
        buff_tracker: BuffTracker,
        ignore_windows,
        buff_names,
        start_time=0,
        max_duration=None,
    ):
        self._start_time = start_time
        self._end_time = end_time
        self._max_duration = max_duration
        self._buff_tracker = buff_tracker
        self._ignore_windows = ignore_windows

        if isinstance(buff_names, set):
            self._buff_names = buff_names
        else:
            self._buff_names = {buff_names}

    def _get_windows(self):
        for buff_name in self._buff_names:
            for window in self._buff_tracker.get_windows(buff_name):
                yield window

    def set_start_time(self, start_time):
        self._start_time = start_time

    def _clamp_windows(self, windows):
        clamped_windows = []

        for i, window in enumerate(windows):
            if not range_overlap(
                (window.start, window.end), (self._start_time, self._end_time)
            ):
                continue

            clamped_window = Window(window.start, window.end)
            if window.end > self._end_time:
                clamped_window.end = self._end_time
            if window.start < self._start_time:
                clamped_window.start = self._start_time
            clamped_windows.append(clamped_window)

        return clamped_windows

    def uptime(self):
        windows = list(self._get_windows())
        windows = self._clamp_windows(windows)
        ignore_windows = self._clamp_windows(self._ignore_windows)
        total_duration = self._end_time - self._start_time

        uptime = calculate_uptime(
            windows, ignore_windows, total_duration, self._max_duration
        )
        return min(1, uptime)

    def score(self):
        return self.uptime()


class CoreAnalysisScorer(AnalysisScorer):
    def get_score_weights(self):
        return {
            GCDAnalyzer: {
                "weight": 3,
            },
            BuffTracker: {
                "weight": 1,
            },
            BombAnalyzer: {
                "weight": 2,
            },
            SynapseSpringsAnalyzer: {
                "weight": 2,
            },
            MeleeUptimeAnalyzer: {
                "weight": 5,
            },
            TrinketAnalyzer: {
                "weight": lambda ta: ta.num_on_use_trinkets,
            },
        }

    def report(self):
        return {
            "analysis_scores": {
                "total_score": self.score(),
            }
        }


class CoreAnalysisConfig:
    show_procs = False
    show_speed = False

    def get_analyzers(self, fight: Fight, buff_tracker, dead_zone_analyzer, items):
        return [
            GCDAnalyzer(fight.source.id, buff_tracker),
            RPAnalyzer(),
            CoreAbilities(),
            BombAnalyzer(fight.duration),
            SynapseSpringsAnalyzer(fight.duration),
            MeleeUptimeAnalyzer(fight.duration, dead_zone_analyzer.get_dead_zones()),
            TrinketAnalyzer(fight.duration, items),
        ]

    def get_scorer(self, analyzers):
        return CoreAnalysisScorer(analyzers)

    def create_rune_tracker(self) -> RuneTracker:
        return RuneTracker(
            should_convert_blood=False,
            should_convert_frost=False,
        )
