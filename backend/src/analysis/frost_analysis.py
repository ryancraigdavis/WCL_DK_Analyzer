from typing import List

from analysis.base import AnalysisScorer, BaseAnalyzer, Window, ScoreWeight
from analysis.core_analysis import (
    BuffTracker,
    CoreAnalysisConfig,
    DiseaseAnalyzer,
    GCDAnalyzer,
    SynapseSpringsAnalyzer,
    MeleeUptimeAnalyzer,
    RuneTracker,
    TrinketAnalyzer,
    RPAnalyzer,
    CoreAbilities,
    BloodChargeCapAnalyzer,
    SoulReaperAnalyzer,
    EmpoweredRuneWeaponAnalyzer,
    BuffUptimeAnalyzer,
    ArmyAnalyzer,
    PlagueLeechAnalyzer,
)
from analysis.unholy_analysis import BloodPlagueAnalyzer, FrostFeverAnalyzer
from console_table import console
from report import Fight


class KMAnalyzer(BaseAnalyzer):
    class Window:
        def __init__(self, timestamp):
            self.gained_timestamp = timestamp
            self.used_timestamp = None
            self.consuming_ability = None
            self.consuming_ability_timestamp = None

    def __init__(self):
        self._windows = []
        self._window = None
        self._km_usage_events = []  # For timeline display
        self._km_on_frost_strike = 0
        self._km_on_obliterate = 0

    def add_event(self, event):
        # Track KM buff events
        if event.get("ability") == "Killing Machine":
            if event["type"] in ("refreshbuff", "applybuff"):
                self._window = self.Window(event["timestamp"])
                self._windows.append(self._window)
            # Could have no window if a previous KM proc was carried over
            elif event["type"] == "removebuff" and self._window:
                if event["timestamp"] - self._window.gained_timestamp < 30000:
                    self._window.used_timestamp = event["timestamp"]
                self._window = None
            return

        # Track abilities that consume KM procs
        if (event["type"] == "cast" and
            event["ability"] in ("Obliterate", "Frost Strike") and
            event.get("consumes_km") and
            self._window):

            # Record what ability consumed the KM proc
            self._window.consuming_ability = event["ability"]
            self._window.consuming_ability_timestamp = event["timestamp"]

            # Count KM usage by ability type
            if event["ability"] == "Frost Strike":
                self._km_on_frost_strike += 1
            elif event["ability"] == "Obliterate":
                self._km_on_obliterate += 1

            # Calculate delay for this usage
            delay = event["timestamp"] - self._window.gained_timestamp

            # Create timeline event for KM usage timing
            km_usage_event = {
                "timestamp": event["timestamp"],
                "type": "km_usage_timing",
                "ability": event["ability"],
                "sourceID": event.get("sourceID"),
                "targetID": event.get("targetID"),
                "km_delay_ms": delay,
                "message": f"{event['ability']} used KM proc after {delay}ms",
                "buffs": [],
                "debuffs": [],
                "runes_before": [],
                "runes": [],
                "runic_power": 0,
                "modifies_runes": False,
                "has_gcd": False,
                "ability_type": 0,
            }
            self._km_usage_events.append(km_usage_event)

    def print(self):
        report = self.report()["killing_machine"]

        if report["num_total"]:
            console.print(
                f"* You used {report['num_used']} of {report['num_total']} Killing Machine procs"
            )
            console.print(
                f"* Your average Killing Machine proc usage delay was {report['avg_time_seconds']:.2f} seconds"
            )
            console.print(
                f"* Total time to use KM procs across fight: {report['total_time_seconds']:.1f} seconds"
            )
        else:
            console.print("* You did not use any Killing Machine procs")

    def get_data(self):
        used_windows = [window for window in self._windows if window.used_timestamp]
        num_windows = len(self._windows)
        num_used = len(used_windows)
        latencies = [
            window.used_timestamp - window.gained_timestamp for window in used_windows
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        total_time_to_use = sum(latencies)  # Total time across all KM procs
        return num_used, num_windows, avg_latency, total_time_to_use, self._km_on_frost_strike, self._km_on_obliterate

    def score(self):
        num_used, num_windows, avg_latency, _, km_on_fs, km_on_obliterate = self.get_data()
        if avg_latency < 1800:
            return 1
        if avg_latency < 1900:
            return 0.9
        if avg_latency < 2000:
            return 0.8
        if avg_latency < 2100:
            return 0.7
        if avg_latency < 2200:
            return 0.6
        if avg_latency < 2300:
            return 0.5
        if avg_latency < 2500:
            return 0.4
        if avg_latency < 3000:
            return 0.2
        return 0

    def report(self):
        num_used, num_windows, avg_latency, total_time_to_use, km_on_fs, km_on_obliterate = self.get_data()

        # Get detailed window information for analysis
        used_windows = [window for window in self._windows if window.used_timestamp]
        window_details = []

        for window in used_windows:
            delay = window.used_timestamp - window.gained_timestamp
            window_details.append({
                "gained_at": window.gained_timestamp,
                "used_at": window.used_timestamp,
                "delay_ms": delay,
                "consuming_ability": window.consuming_ability,
            })

        # Calculate Frost Strike percentage for scoring
        total_km_used = km_on_fs + km_on_obliterate
        fs_percentage = (km_on_fs / total_km_used) if total_km_used > 0 else 0

        return {
            "killing_machine": {
                "num_used": num_used,
                "num_total": num_windows,
                "avg_latency": avg_latency,
                "total_time_to_use": total_time_to_use,  # Total time across whole fight
                "avg_time_seconds": avg_latency / 1000,  # Average time in seconds for UI
                "total_time_seconds": total_time_to_use / 1000,  # Total time in seconds for UI
                "windows": window_details,
                "usage_events": self._km_usage_events,  # For timeline integration
                "km_on_frost_strike": km_on_fs,
                "km_on_obliterate": km_on_obliterate,
                "frost_strike_percentage": fs_percentage,
            },
        }




class HowlingBlastAnalyzer(BaseAnalyzer):
    def __init__(self):
        self._bad_usages = 0

    def add_event(self, event):
        if event["type"] == "cast" and event["ability"] == "Howling Blast":
            if event["num_targets"] >= 3 or event["consumes_rime"]:
                is_bad = False
            elif event["num_targets"] == 2 and event["consumes_km"]:
                is_bad = False
            else:
                is_bad = True

            event["bad_howling_blast"] = is_bad
            if is_bad:
                self._bad_usages += 1

    def print(self):
        if self._bad_usages:
            console.print(
                "[red]x[/red] You used Howling Blast without Rime"
                f" on less than 3 targets {self._bad_usages} times"
            )
        else:
            console.print(
                "[green]✓[/green] You always used Howling Blast with rime or on 3+ targets"
            )

    def score(self):
        if self._bad_usages == 0:
            return 1
        if self._bad_usages == 1:
            return 0.5
        return 0

    def report(self):
        return {
            "howling_blast_bad_usages": {
                "num_bad_usages": self._bad_usages,
            }
        }


class RimeAnalyzer(BaseAnalyzer):
    def __init__(self, buff_tracker: BuffTracker):
        self._num_total = 1 if buff_tracker.is_active("Rime", 0) else 0
        self._num_used = 0

    def add_event(self, event):
        if event["type"] in ("applybuff", "refreshbuff") and event["ability"] == "Rime":
            self._num_total += 1
        if event.get("consumes_rime"):
            self._num_used += 1

    def score(self):
        # bug with Razorscale, can start with rime
        total = max(self._num_total, self._num_used)

        if not total:
            return 0
        return 1 * (self._num_used / total)

    def report(self):
        return {
            "rime": {
                "num_total": self._num_total,
                "num_used": self._num_used,
            }
        }


class RaiseDeadWindow(Window):
    def __init__(
        self,
        start,
        fight_duration,
        buff_tracker: BuffTracker,
        ignore_windows,
        items,
    ):
        self.start = start
        # Frost ghoul lasts for 60 seconds (or until dismissed/killed)
        self.end = min(start + 60000, fight_duration)
        self._ghoul_first_attack = None

        # Dynamic buff tracking for MoP (similar to gargoyle)
        self._synapse_springs_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Synapse Springs",
            self.start,
            max_duration=10000 - 25,
        )
        self._fallen_crusader_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Unholy Strength",
            self.start,
            max_duration=15000 - 25,
        )
        self._potion_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Potion of Mogu Power",
            self.start,
            max_duration=25000 - 25,
        )
        self._bloodfury_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Blood Fury",
            self.start,
            max_duration=15000 - 25,
        )
        self._berserking_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Berserking",
            self.start,
            max_duration=10000 - 25,
        )
        self._bloodlust_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            {"Bloodlust", "Heroism", "Time Warp"},
            self.start,
            max_duration=40000 - 25,
        )
        self._pillar_of_frost_uptime = BuffUptimeAnalyzer(
            self.end,
            buff_tracker,
            ignore_windows,
            "Pillar of Frost",
            self.start,
            max_duration=20000 - 25,
        )

        # Collect all uptimes for event passing
        self._uptimes = [
            self._synapse_springs_uptime,
            self._fallen_crusader_uptime,
            self._potion_uptime,
            self._bloodfury_uptime,
            self._berserking_uptime,
            self._bloodlust_uptime,
            self._pillar_of_frost_uptime,
        ]

        self.num_attacks = 0
        self.total_damage = 0
        self._items = items
        self._all_trinkets = []
        self.trinket_uptimes = []
        self._ghoul_source_id = None  # Will be set by the analyzer

        # Track trinkets that affect pets
        for trinket in self._items.trinkets:
            if trinket.uptime_ghoul:  # Reuse the ghoul trinket flag
                self._all_trinkets.append(trinket)

        for trinket in self._all_trinkets:
            uptime = BuffUptimeAnalyzer(
                self.end,
                buff_tracker,
                ignore_windows,
                trinket.buff_name,
                self.start,
                max_duration=trinket.proc_duration - 25,
            )
            self._uptimes.append(uptime)
            self.trinket_uptimes.append({
                "trinket": trinket,
                "uptime": uptime,
            })

    def _set_ghoul_first_attack(self, event):
        self._ghoul_first_attack = event["timestamp"]
        # Set start time for all uptime analyzers when ghoul first attacks
        for uptime in self._uptimes:
            uptime.set_start_time(event["timestamp"])

    # Properties for frontend compatibility
    @property
    def synapse_springs_uptime(self):
        return self._synapse_springs_uptime.uptime()

    @property
    def fallen_crusader_uptime(self):
        return self._fallen_crusader_uptime.uptime()

    @property
    def potion_uptime(self):
        return self._potion_uptime.uptime()

    @property
    def bloodfury_uptime(self):
        return self._bloodfury_uptime.uptime()

    @property
    def berserking_uptime(self):
        return self._berserking_uptime.uptime()

    @property
    def bloodlust_uptime(self):
        return self._bloodlust_uptime.uptime()

    @property
    def pillar_of_frost_uptime(self):
        return self._pillar_of_frost_uptime.uptime()

    @property
    def trinket_snapshots(self):
        # Convert trinket uptimes to snapshot-style format for frontend compatibility
        return [
            {
                "trinket": trinket_data["trinket"],
                "name": trinket_data["trinket"].name,
                "icon": trinket_data["trinket"].icon,
                "did_snapshot": trinket_data["uptime"].uptime() > 0,
                "uptime": trinket_data["uptime"].uptime(),
            }
            for trinket_data in self.trinket_uptimes
        ]

    def add_event(self, event):
        # Pass events to all uptime analyzers
        for uptime in self._uptimes:
            uptime.add_event(event)

        # Track ghoul attacks and damage using the tracked sourceID
        if self._ghoul_source_id and event.get("sourceID") == self._ghoul_source_id:
            if (
                event["type"] in ("cast", "startcast", "damage")
                and self._ghoul_first_attack is None
            ):
                self._set_ghoul_first_attack(event)

            if event["type"] == "damage":
                self.num_attacks += 1
                self.total_damage += event["amount"]

    def score(self):
        # Score based on buff uptime during ghoul window
        ghoul_duration = self.end - self.start  # 60 seconds max

        return ScoreWeight.calculate(
            ScoreWeight(self.synapse_springs_uptime / ghoul_duration, 2),
            ScoreWeight(self.fallen_crusader_uptime / ghoul_duration, 3),
            ScoreWeight(self.potion_uptime / ghoul_duration, 3),
            ScoreWeight(self.pillar_of_frost_uptime / ghoul_duration, 4),
            # Performance score based on attacks
            ScoreWeight(min(1, self.num_attacks / 30), 3), # Expect ~30 attacks in 60s
            # Trinket uptime score
            ScoreWeight(
                sum(t["uptime"] for t in self.trinket_snapshots) /
                (ghoul_duration * len(self.trinket_snapshots)) if self.trinket_snapshots else 0,
                len(self.trinket_snapshots) * 2,
            ),
            # Blood Fury uptime score
            ScoreWeight(
                self.bloodfury_uptime / ghoul_duration if self._bloodfury_uptime else 0,
                2 if self._bloodfury_uptime else 0,
            ),
            # Berserking uptime score
            ScoreWeight(
                self.berserking_uptime / ghoul_duration if self._berserking_uptime else 0,
                2 if self._berserking_uptime else 0,
            ),
            # Bloodlust uptime score
            ScoreWeight(
                self.bloodlust_uptime / ghoul_duration if self._bloodlust_uptime else 0,
                3 if self._bloodlust_uptime else 0,
            ),
        )


class RaiseDeadAnalyzer(BaseAnalyzer):
    INCLUDE_PET_EVENTS = True

    def __init__(self, fight_duration, buff_tracker, ignore_windows, items):
        self.windows: List[RaiseDeadWindow] = []
        self._window = None
        self._buff_tracker = buff_tracker
        self._fight_duration = fight_duration
        self._ignore_windows = ignore_windows
        self._items = items
        self._ghoul_source_id = None  # Track the ghoul's sourceID

    def add_event(self, event):
        # Check for Raise Dead by ability ID - 46585 is the Frost DK version
        if event["type"] in ("cast", "summon") and event.get("abilityGameID") in (46585, 52150):
            self._window = RaiseDeadWindow(
                event["timestamp"],
                self._fight_duration,
                self._buff_tracker,
                self._ignore_windows,
                self._items,
            )
            self.windows.append(self._window)

            # Track the ghoul's sourceID from the summon event's targetID
            if event["type"] == "summon":
                self._ghoul_source_id = event.get("targetID")
                self._window._ghoul_source_id = self._ghoul_source_id

        if not self._window:
            return

        # Only process events within the ghoul window timeframe
        if event["timestamp"] <= self._window.end:
            self._window.add_event(event)

    @property
    def possible_raise_deads(self):
        return max(1 + (self._fight_duration - 20000) // 183000, len(self.windows))

    def score(self):
        window_score = sum(window.score() for window in self.windows)
        return ScoreWeight.calculate(
            ScoreWeight(
                window_score / self.possible_raise_deads, 5 * self.possible_raise_deads
            ),
        )

    def report(self):
        return {
            "raise_dead": {
                "score": self.score(),
                "num_possible": self.possible_raise_deads,
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
                        "synapse_springs_uptime": window.synapse_springs_uptime,
                        "potion_uptime": window.potion_uptime,
                        "fallen_crusader_uptime": window.fallen_crusader_uptime,
                        "bloodfury_uptime": window.bloodfury_uptime,
                        "berserking_uptime": window.berserking_uptime,
                        "bloodlust_uptime": window.bloodlust_uptime,
                        "pillar_of_frost_uptime": window.pillar_of_frost_uptime,
                        "num_attacks": window.num_attacks,
                        "start": window.start,
                        "end": window.end,
                        "trinket_snapshots": [
                            {
                                "name": t["trinket"].name,
                                "did_snapshot": t["did_snapshot"],
                                "icon": t["trinket"].icon,
                                "uptime": t["uptime"],
                            }
                            for t in window.trinket_snapshots
                        ],
                    }
                    for window in self.windows
                ],
            }
        }


class ObliterateAnalyzer(BaseAnalyzer):
    def __init__(self, fight_end_time, ignore_windows):
        self._obliterates_during_rime = 0
        self._obliterates_with_death_runes = 0
        self._total_obliterates = 0
        self._fight_end_time = fight_end_time
        self._ignore_windows = ignore_windows
        self._death_rune_events = []  # For timeline display

    def add_event(self, event):
        if (
            event["type"] == "cast"
            and event["ability"] == "Obliterate"
            and not event["is_miss"]
        ):
            self._total_obliterates += 1

            # Check if Obliterate was cast during Rime (which is bad for Masterfrost)
            active_buffs = event.get("buffs", [])
            has_rime = any(buff["ability"] == "Rime" for buff in active_buffs)

            if has_rime:
                self._obliterates_during_rime += 1

            # Check if Obliterate used non-Death runes when Death runes were available
            runes_before = event.get("runes_before", [])
            runes_after = event.get("runes", [])
            if runes_before and runes_after:
                # Count available runes before the cast
                unholy_available = sum(1 for rune in runes_before if rune["name"] == "Unholy" and rune["is_available"])
                frost_available = sum(1 for rune in runes_before if rune["name"] == "Frost" and rune["is_available"])
                death_available = sum(1 for rune in runes_before if rune["name"] == "Death" and rune["is_available"])

                # Count what runes were actually consumed (became unavailable)
                unholy_consumed = sum(1 for i, rune in enumerate(runes_before)
                                    if (rune["name"] == "Unholy" and rune["is_available"] and
                                        not runes_after[i]["is_available"]))
                frost_consumed = sum(1 for i, rune in enumerate(runes_before)
                                   if (rune["name"] == "Frost" and rune["is_available"] and
                                       not runes_after[i]["is_available"]))
                death_consumed = sum(1 for i, rune in enumerate(runes_before)
                                   if (rune["name"] == "Death" and rune["is_available"] and
                                       not runes_after[i]["is_available"]))

                # Obliterate costs 1 Unholy + 1 Frost, but Death runes can substitute for either
                total_consumed = unholy_consumed + frost_consumed + death_consumed

                # Bad usage: any Obliterate that doesn't use an Unholy rune is suboptimal
                if total_consumed == 2:
                    is_bad_usage = False
                    message_parts = []

                    # Only valid combinations are those that include an Unholy rune:
                    # - Death + Unholy ✅
                    # - Frost + Unholy ✅
                    # Everything else is bad:
                    # - Death + Frost ❌
                    # - Death + Death ❌

                    if unholy_consumed == 0:
                        is_bad_usage = True
                        if death_consumed == 2:
                            message_parts.append(f"Used 2 Death runes instead of Death+Unholy or Frost+Unholy")
                        elif death_consumed > 0 and frost_consumed > 0:
                            message_parts.append(f"Used Death+Frost instead of Death+Unholy or Frost+Unholy")

                    if is_bad_usage:
                        self._obliterates_with_death_runes += 1

                        # Create simplified timeline message showing what runes were used
                        if frost_consumed > 0 and unholy_consumed > 0:
                            rune_description = "Frost and Unholy"
                        elif death_consumed == 2:
                            rune_description = "2 Deaths"
                        elif death_consumed > 0 and frost_consumed > 0:
                            rune_description = "Death and Frost"
                        else:
                            rune_description = f"{unholy_consumed}U, {frost_consumed}F, {death_consumed}D"

                        death_rune_event = {
                            "timestamp": event["timestamp"],
                            "type": "obliterate_death_rune_usage",
                            "ability": "Obliterate",
                            "sourceID": event.get("sourceID"),
                            "targetID": event.get("targetID"),
                            "message": f"Obliterate used with {rune_description}",
                            "buffs": [],
                            "debuffs": [],
                            "runes_before": [],
                            "runes": [],
                            "runic_power": 0,
                            "modifies_runes": False,
                            "has_gcd": False,
                            "ability_type": 0,
                        }
                        self._death_rune_events.append(death_rune_event)

    def score(self):
        # For Masterfrost: 0 obliterates during Rime and 0 death rune usage = perfect score
        if self._obliterates_during_rime == 0 and self._obliterates_with_death_runes == 0:
            return 1
        # Partial penalty for each type of bad usage
        total_bad_usages = self._obliterates_during_rime + self._obliterates_with_death_runes
        if total_bad_usages == 1:
            return 0.5
        return 0

    def report(self):
        return {
            "obliterate_during_rime": {
                "bad_usages": self._obliterates_during_rime,
                "total_obliterates": self._total_obliterates,
            },
            "obliterate_death_rune_usage": {
                "bad_usages": self._obliterates_with_death_runes,
                "total_obliterates": self._total_obliterates,
                "death_rune_events": self._death_rune_events,
            }
        }


class PillarOfFrostAnalyzer(BaseAnalyzer):
    def __init__(self, fight_duration):
        self._pillar_casts = []
        self._fight_duration = fight_duration

    def add_event(self, event):
        if event["type"] == "cast" and event["ability"] == "Pillar of Frost":
            self._pillar_casts.append(event["timestamp"])

    @property
    def possible_pillars(self):
        # First pillar available immediately, then every 60 seconds
        # Calculate how many 60-second windows fit in the fight duration
        return 1 + (self._fight_duration // 60000)

    def score(self):
        usage_percentage = len(self._pillar_casts) / self.possible_pillars if self.possible_pillars > 0 else 0

        if usage_percentage >= 1.0:
            return 1
        elif usage_percentage >= 0.9:
            return 0.8
        else:
            return 0.4

    def report(self):
        return {
            "pillar_of_frost_usage": {
                "num_used": len(self._pillar_casts),
                "possible_usages": self.possible_pillars,
                "usage_percentage": len(self._pillar_casts) / self.possible_pillars if self.possible_pillars > 0 else 0,
            }
        }


class PlagueStrikeAnalyzer(BaseAnalyzer):
    def __init__(self):
        self._plague_strikes_with_death_runes = 0
        self._total_plague_strikes = 0
        self._death_rune_events = []  # For timeline display

    def add_event(self, event):
        if (
            event["type"] == "cast"
            and event["ability"] == "Plague Strike"
            and not event.get("is_miss", False)
        ):
            self._total_plague_strikes += 1

            # Check if Plague Strike used Death runes instead of Unholy runes
            runes_before = event.get("runes_before", [])
            runes_after = event.get("runes", [])
            if runes_before and runes_after:
                # Count available runes before the cast
                unholy_available = sum(1 for rune in runes_before if rune["name"] == "Unholy" and rune["is_available"])
                death_available = sum(1 for rune in runes_before if rune["name"] == "Death" and rune["is_available"])

                # Count what runes were actually consumed (became unavailable)
                unholy_consumed = sum(1 for i, rune in enumerate(runes_before)
                                    if (rune["name"] == "Unholy" and rune["is_available"] and
                                        not runes_after[i]["is_available"]))
                death_consumed = sum(1 for i, rune in enumerate(runes_before)
                                   if (rune["name"] == "Death" and rune["is_available"] and
                                       not runes_after[i]["is_available"]))

                # Plague Strike costs 1 Unholy rune - check if Death rune was used instead
                if death_consumed > 0 and unholy_available > 0:
                    self._plague_strikes_with_death_runes += 1

                    # Create timeline event for bad Death rune usage
                    death_rune_event = {
                        "timestamp": event["timestamp"],
                        "type": "plague_strike_death_rune_usage",
                        "ability": "Plague Strike",
                        "sourceID": event.get("sourceID"),
                        "targetID": event.get("targetID"),
                        "message": "Plague Strike casted with Death rune",
                        "buffs": [],
                        "debuffs": [],
                        "runes_before": [],
                        "runes": [],
                        "runic_power": 0,
                        "modifies_runes": False,
                        "has_gcd": False,
                        "ability_type": 0,
                    }
                    self._death_rune_events.append(death_rune_event)

    def score(self):
        # Perfect score if no Death rune usage
        if self._plague_strikes_with_death_runes == 0:
            return 1
        # Partial penalty for bad usage
        if self._plague_strikes_with_death_runes == 1:
            return 0.5
        return 0

    def report(self):
        return {
            "plague_strike_death_rune_usage": {
                "bad_usages": self._plague_strikes_with_death_runes,
                "total_plague_strikes": self._total_plague_strikes,
                "death_rune_events": self._death_rune_events,
            }
        }


class FrostAnalysisScorer(AnalysisScorer):
    def get_score_weights(self):
        return {
            ObliterateAnalyzer: {
                "weight": 2,  # Reduced weight since it's now pass/fail rather than CPM optimization
            },
            KMAnalyzer: {
                "weight": 1,
            },
            DiseaseAnalyzer: {
                "weight": 2,
            },
            BloodPlagueAnalyzer: {
                "weight": 3,
                "exponent_factor": 1.5,
            },
            FrostFeverAnalyzer: {
                "weight": 3,
                "exponent_factor": 1.5,
            },
            MeleeUptimeAnalyzer: {
                "weight": 2,
                "exponent_factor": 1.5,
            },
            SynapseSpringsAnalyzer: {
                "weight": 1,
            },
            CoreAbilities: {
                "weight": 0,  # This is just for event decoration, no score impact
            },
            BloodChargeCapAnalyzer: {
                "weight": 1,
            },
            PillarOfFrostAnalyzer: {
                "weight": 2,
            },
            PlagueStrikeAnalyzer: {
                "weight": 1,
            },
        }

    def report(self):
        return {
            "analysis_scores": {
                "total_score": self.score(),
            }
        }


class FrostAnalysisConfig(CoreAnalysisConfig):
    show_procs = True
    show_speed = True

    def get_analyzers(self, fight: Fight, buff_tracker, dead_zone_analyzer, items):
        dead_zones = dead_zone_analyzer.get_dead_zones()
        combatant_info = fight.get_combatant_info(fight.source.id)
        return super().get_analyzers(fight, buff_tracker, dead_zone_analyzer, items) + [
            DiseaseAnalyzer(fight.encounter.name, fight.duration),
            BloodPlagueAnalyzer(fight.duration, dead_zones),
            FrostFeverAnalyzer(fight.duration, dead_zones),
            KMAnalyzer(),
            HowlingBlastAnalyzer(),
            RimeAnalyzer(buff_tracker),
            RaiseDeadAnalyzer(fight.duration, buff_tracker, dead_zones, items),
            ObliterateAnalyzer(fight.duration, dead_zones),
            PillarOfFrostAnalyzer(fight.duration),
            PlagueStrikeAnalyzer(),
            ArmyAnalyzer(fight.duration, buff_tracker, dead_zones, items),
            PlagueLeechAnalyzer(fight.duration, combatant_info),
        ]

    def get_scorer(self, analyzers, fight=None):
        return FrostAnalysisScorer(analyzers)

    def create_rune_tracker(self):
        return RuneTracker(
            should_convert_blood=False,
            should_convert_frost=False,
            start_with_death_runes=True,  # MoP: Frost DKs start with 2 death runes
        )
