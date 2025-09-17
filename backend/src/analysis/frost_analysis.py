from analysis.base import AnalysisScorer, BaseAnalyzer, Window
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
)
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


class RaiseDeadAnalyzer(BaseAnalyzer):
    def __init__(self, fight_end_time):
        self._num_raise_deads = 0
        self._fight_end_time = fight_end_time

    @property
    def possible_raise_deads(self):
        return max(1 + (self._fight_end_time - 20000) // 183000, self._num_raise_deads)

    def add_event(self, event):
        if event["type"] == "cast" and event["ability"] == "Raise Dead":
            self._num_raise_deads += 1

    def score(self):
        return self._num_raise_deads / self.possible_raise_deads

    def report(self):
        return {
            "raise_dead_usage": {
                "num_usages": self._num_raise_deads,
                "possible_usages": self.possible_raise_deads,
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

                # Bad usage: using non-Death runes when Death runes are available
                if total_consumed == 2 and death_available > 0:
                    is_bad_usage = False
                    message_parts = []

                    # Case 1: Used Frost + Unholy when Death was available (should use Death + Unholy)
                    if frost_consumed > 0 and unholy_consumed > 0 and death_consumed == 0:
                        is_bad_usage = True
                        message_parts.append(f"Used Frost+Unholy instead of Death+Unholy")

                    # Case 2: Used 2 Death runes when other runes were available
                    elif death_consumed == 2 and (unholy_available > 0 or frost_available > 0):
                        is_bad_usage = True
                        message_parts.append(f"Used 2 Death runes unnecessarily")

                    # Case 3: Used Death + Frost when Unholy was available
                    elif death_consumed > 0 and frost_consumed > 0 and unholy_available > 0:
                        is_bad_usage = True
                        message_parts.append(f"Used Death+Frost instead of Death+Unholy")

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
            GCDAnalyzer: {
                "weight": 3,
            },
            KMAnalyzer: {
                "weight": 1,
            },
            DiseaseAnalyzer: {
                "weight": 2,
            },
            HowlingBlastAnalyzer: {
                "weight": 0.5,
            },
            RimeAnalyzer: {
                "weight": 0.5,
            },
            RaiseDeadAnalyzer: {
                "weight": lambda rd: rd.possible_raise_deads,
            },
            MeleeUptimeAnalyzer: {
                "weight": 4,
                "exponent_factor": 1.5,
            },
            BuffTracker: {
                "weight": 1,
            },
            SynapseSpringsAnalyzer: {
                "weight": 1,
            },
            TrinketAnalyzer: {
                "weight": 1,
            },
            RPAnalyzer: {
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
            SoulReaperAnalyzer: {
                "weight": 1,
            },
            PlagueStrikeAnalyzer: {
                "weight": 1,
            },
            EmpoweredRuneWeaponAnalyzer: {
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
        return super().get_analyzers(fight, buff_tracker, dead_zone_analyzer, items) + [
            DiseaseAnalyzer(fight.encounter.name, fight.duration),
            KMAnalyzer(),
            HowlingBlastAnalyzer(),
            RimeAnalyzer(buff_tracker),
            RaiseDeadAnalyzer(fight.duration),
            ObliterateAnalyzer(fight.duration, dead_zone_analyzer.get_dead_zones()),
            PillarOfFrostAnalyzer(fight.duration),
            PlagueStrikeAnalyzer(),
        ]

    def get_scorer(self, analyzers):
        return FrostAnalysisScorer(analyzers)

    def create_rune_tracker(self):
        return RuneTracker(
            should_convert_blood=False,
            should_convert_frost=False,
        )
