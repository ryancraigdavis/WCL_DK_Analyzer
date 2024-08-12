from analysis.core_analysis import (
    PrepullArmyOfTheDeadTracker,
    CoreAnalysisConfig,
    DeadZoneAnalyzer,
    TalentPreprocessor,
    BuffTracker,
    PetNameDetector,
    RuneHasteTracker,
)
from analysis.frost_analysis import (
    FrostAnalysisConfig,
)
from analysis.items import ItemPreprocessor, TrinketPreprocessor
from analysis.unholy_analysis import UnholyAnalysisConfig
from report import Fight, Report


class Analyzer:
    SPEC_ANALYSIS_CONFIGS = {
        "Default": CoreAnalysisConfig,
        "Frost": FrostAnalysisConfig,
        "Unholy": UnholyAnalysisConfig,
    }

    def __init__(self, fight: Fight):
        self._fight = fight
        self._events = self._filter_events()
        self.__spec = None
        self._analysis_config = self.SPEC_ANALYSIS_CONFIGS.get(
            self._detect_spec(),
            self.SPEC_ANALYSIS_CONFIGS["Default"],
        )()
        self._buff_tracker = None
        self.runes = None

    def _preprocess_events(self):
        dead_zone_analyzer = self._get_dead_zone_analyzer()
        talent_preprocessor = self._get_talent_preprocessor()
        buff_tracker = self._get_buff_tracker()
        source_id = self._fight.source.id
        pet_analyzer = PetNameDetector()
        items = self._get_item_preprocessor()
        aotd = PrepullArmyOfTheDeadTracker(self.runes)

        for event in self._events:
            if event["sourceID"] == source_id or event["targetID"] == source_id:
                dead_zone_analyzer.preprocess_event(event)
                talent_preprocessor.preprocess_event(event)
                buff_tracker.preprocess_event(event)
                items.preprocess_event(event)

            # Pet analyzers
            pet_analyzer.preprocess_event(event)
            aotd.preprocess_event(event)

        for event in self._events:
            dead_zone_analyzer.decorate_event(event)
            buff_tracker.decorate_event(event)
            talent_preprocessor.decorate_event(event)
            items.decorate_event(event)
            pet_analyzer.decorate_event(event)
            aotd.decorate_event(event)

        return dead_zone_analyzer

    def _get_dead_zone_analyzer(self):
        if not hasattr(self, "_dead_zone_analyzer"):
            self._dead_zone_analyzer = DeadZoneAnalyzer(self._fight)
        return self._dead_zone_analyzer

    def _get_talent_preprocessor(self):
        if not hasattr(self, "_talent_preprocessor"):
            self._talent_preprocessor = TalentPreprocessor(
                self._fight.get_combatant_info(self._fight.source.id)
            )
        return self._talent_preprocessor

    def _get_item_preprocessor(self):
        if not hasattr(self, "_item_preprocessor"):
            self._item_preprocessor = ItemPreprocessor(
                self._fight.get_combatant_info(self._fight.source.id)
            )
        return self._item_preprocessor

    def _create_rune_haste_tracker(self, runes) -> RuneHasteTracker:
        combatant_info = self._fight.get_combatant_info(self._fight.source.id)
        buff_tracker = self._get_buff_tracker()
        return RuneHasteTracker(combatant_info, buff_tracker, runes)

    def _get_buff_tracker(self):
        if self._buff_tracker is None:
            source_id = self._fight.source.id
            combatant_info = self._fight.get_combatant_info(source_id)
            starting_auras = combatant_info.get("auras", [])

            self._buff_tracker = BuffTracker(
                {
                    "Pillar of Frost",
                    "Heroism",
                    "Bloodlust",
                    "Time Warp",
                    "Slayer",
                    "Thrill of Victory",
                    "Heartened",
                    "Race Against Death",
                    "Eye of Doom",
                    "Typhoon",
                    "Polarization",
                    "King of Boars",
                    "Fatality",
                    "Golem's Strength",
                    "Rime",
                    "Synapse Springs",
                    "Sudden Doom",
                    "Killing Machine",
                    "Berserking",
                    "Blood Fury",
                    "Swordguard Embroidery",
                    "Unholy Strength",
                    "Stolen Power",
                    "Free Your Mind",
                    "Cinderglacier",
                    "Death Eater",  # T11 4pc
                    "Smoldering Rune",  # T12 2pc
                    "Runic Corruption",
                    "Unholy Frenzy",
                    "Flask of Titanic Strength",
                    "Flask of Battle",
                    "Blood Presence",
                    "Unholy Presence",
                    "Frost Presence",
                }
                | set(TrinketPreprocessor.TRINKEY_MAP_BY_BUFF_NAME.keys()),
                self._fight.duration,
                starting_auras,
                self._detect_spec(),
            )
        return self._buff_tracker

    def _detect_spec(self):
        if not self.__spec:

            def detect():
                for event in self._events:
                    if event["type"] == "cast" and event["ability"] in (
                        "Howling Blast",
                        "Frost Strike",
                    ):
                        return "Frost"
                    if event["type"] == "cast" and event["ability"] in (
                        "Summon Gargoyle",
                        "Unholy Frenzy",
                    ):
                        return "Unholy"

                return None

            self.__spec = detect()
        return self.__spec

    def _filter_events(self):
        """Remove any events we don't care to analyze or show"""
        events = []

        for i, event in enumerate(self._fight.events):
            # We're neither the source nor the target
            if (
                event["sourceID"] != self._fight.source.id
                and event["targetID"] != self._fight.source.id
                and event["sourceID"] not in self._fight.source.pets
                and event["targetID"] not in self._fight.source.pets
            ):
                continue

            # Don't really care about these
            if event["type"] in ("applydebuffstack",):
                continue

            if (
                event["type"] in ("refreshbuff", "applybuff", "removebuff")
                and event["targetID"] != self._fight.source.id
                and event["targetID"] not in self._fight.source.pets
            ):
                continue

            events.append(event)
        return events

    @property
    def displayable_events(self):
        """Remove any events we don't care to show in the UI"""
        events = []

        for event in self._events:
            if event["sourceID"] == self._fight.source.id and (
                (event["type"] == "cast" and event["ability"] not in ("Speed", "Melee"))
                or (
                    event["type"] == "applybuff"
                    and event["ability"] == "Killing Machine"
                )
                or (
                    event["type"] == "removebuff"
                    and event["ability"] in ("Unbreakable Armor", "Blood Tap")
                )
                or (
                    event["type"] == "removedebuff"
                    and event["ability"] in ("Blood Plague", "Frost Fever")
                    and (
                        self._fight.encounter.name != "Thaddius"
                        or not event["in_dead_zone"]
                    )
                    and event["target_is_boss"]
                )
                or (
                    event["type"] in ("removedebuff", "applydebuff", "refreshdebuff")
                    and event["ability"]
                    in (
                        "Dominion",
                        "Magma",
                    )
                )
            ):
                events.append(event)
        return events

    def analyze(self):
        self.runes = self._analysis_config.create_rune_tracker()
        rune_haste_tracker = self._create_rune_haste_tracker(self.runes)

        self._preprocess_events()

        buff_tracker = self._get_buff_tracker()
        analyzers = [rune_haste_tracker, self.runes, buff_tracker]
        analyzers.extend(
            self._analysis_config.get_analyzers(
                self._fight,
                buff_tracker,
                self._get_dead_zone_analyzer(),
                self._get_item_preprocessor(),
            )
        )
        analyzers.append(self._analysis_config.get_scorer(analyzers))

        source_id = self._fight.source.id
        for event in self._events:
            for analyzer in analyzers:
                if (
                    event["sourceID"] == source_id or event["targetID"] == source_id
                ) or (
                    analyzer.INCLUDE_PET_EVENTS
                    and (event["is_owner_pet_source"] or event["is_owner_pet_target"])
                ):
                    analyzer.add_event(event)

        displayable_events = self.displayable_events
        has_rune_error = any(event.get("rune_spend_error") for event in self._events)
        num_rune_adjustments = sum(
            1 for event in self._events if event.get("rune_spend_adjustment")
        )
        analysis = {
            "has_rune_spend_error": has_rune_error,
            "num_rune_adjustments": num_rune_adjustments,
        }

        for analyzer in analyzers:
            analysis.update(**analyzer.report())

        return {
            "fight_metadata": {
                "source": self._fight.source.name,
                "encounter": self._fight.encounter.name,
                "start_time": self._fight.start_time,
                "end_time": self._fight.end_time,
                "duration": self._fight.end_time - self._fight.start_time,
                "rankings": self._fight.rankings,
            },
            "analysis": analysis,
            "events": displayable_events,
            "spec": self._detect_spec(),
            "show_procs": self._analysis_config.show_procs,
            "show_speed": self._analysis_config.show_speed,
        }


def analyze(report: Report, fight_id: int):
    fight = report.get_fight(fight_id)
    analyzer = Analyzer(fight)
    return analyzer.analyze()
