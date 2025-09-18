import React, {useCallback, useContext } from "react";
import {LogAnalysisContext} from "./LogAnalysisContext.jsx";

import BloodRune from "./assets/blood_rune.webp";
import FrostRune from "./assets/frost_rune.webp";
import UnholyRune from "./assets/unholy_rune.webp";
import DeathRune from "./assets/death_rune.webp";
import { ArmyAnalysis } from "./ArmyAnalysis.jsx"
import { ArmyDynamicAnalysis } from "./ArmyDynamicAnalysis.jsx"
import { GargoyleAnalysis } from "./GargoyleAnalysis"
import { DarkTransformationAnalysis } from "./DarkTransformationAnalysis"
import { GhoulAnalysis } from "./GhoulAnalysis.jsx"
import { RaiseDeadAnalysis } from "./RaiseDeadAnalysis.jsx"
import { SoulReaperAnalysis } from "./SoulReaperAnalysis.jsx"
import { OutbreakAnalysis } from "./OutbreakAnalysis.jsx"
import { Tabs, Tab } from "./Tabs.jsx"
import { formatIcon, formatTimestamp, formatUpTime, formatUsage, Tooltip } from "./helpers"

const formatRune = (rune, i) => {
  const src = {
    Blood: BloodRune,
    Frost: FrostRune,
    Unholy: UnholyRune,
    Death: DeathRune,
  }[rune.name];
  const className = rune.is_available ? "rune rune-available" : "rune rune-cd";

  return (
    <img
      key={i}
      className={className}
      src={src}
      title={rune.name}
      alt={rune.name}
      width={14}
    />
  );
};

const ABILITY_TYPES = new Set([0, 1, 4, 16, 32]);

const getAbilityTypeClass = (abilityType) => {
  if (ABILITY_TYPES.has(abilityType)) {
    return `ability-name ability-type-${abilityType}`;
  }
  return "ability-name ability-type-unknown";
};

const formatRanking = (ranking) => {
  let color = "grey";

  if (ranking === 100) {
    color = "gold";
  } else if (ranking >= 99) {
    color = "pink";
  } else if (ranking >= 95) {
    color = "orange";
  } else if (ranking >= 75) {
    color = "purple";
  } else if (ranking >= 50) {
    color = "blue";
  }

  return <span className={color}>{ranking}</span>;
};

const Summary = () => {
  const analysis = useContext(LogAnalysisContext);

  const formatEvent = useCallback((event, showRunes, showProcs, i) => {
    const abilityIcon = event.ability_icon;
    const icon = abilityIcon ? (
      <img
        src={abilityIcon}
        title={event.ability}
        alt={event.ability}
        width={20}
      />
    ) : null;
    const offset = event.gcd_offset;
    let ability = event.ability;
    let timestamp = <span>{formatTimestamp(event.timestamp)}</span>;
    let runicPower = String(Math.floor(event.runic_power / 10)).padStart(
      3,
      " "
    );
    let bloodCharges = String(event.blood_charges || 0).padStart(2, " ");

    let abilityTdClass = "";
    let abilityDivClass = "ability";
    let rowClass = "";

    if (event.runic_power_waste) {
      const runic_power_waste = Math.floor(event.runic_power_waste / 10);
      runicPower = (
        <>
          {runicPower} <span className={"red"}>(+{runic_power_waste})</span>
        </>
      );
    }

    if (event.type === "removedebuff") {
      abilityTdClass = "debuff-drops";
      ability = `${ability} drops on ${event.target}`;
    }

    if (event.type === "removebuff") {
      abilityTdClass = "buff-drops";
      ability = `${ability} ends`;
    }

    if (event.type === "death_rune_waste") {
      abilityTdClass = "death-rune-waste";
      ability = `${ability} wasted ${event.death_runes_wasted} death rune${event.death_runes_wasted > 1 ? 's' : ''}`;
    }

    if (event.type === "km_usage_timing") {
      abilityTdClass = "km-usage-timing";
      const delaySeconds = (event.km_delay_ms / 1000).toFixed(2);
      ability = `${ability} used KM proc after ${delaySeconds}s`;
    }

    if (event.is_miss) {
      rowClass = "ability-miss";
      ability = (
        <>
          {ability}{" "}
          <span className={"red"}>({event.hit_type.toLowerCase()})</span>
        </>
      );
    }

    if (!event.is_core_cast) {
      abilityDivClass += " filler-cast";
    }

    const hasUnholyPresence = event.buffs.some((buff) => buff.ability === "Unholy Presence")
    const assumedGCD = hasUnholyPresence ? 1000 : 1500

    if (event.has_gcd && offset) {
      let color;
      if (offset - assumedGCD > 500) {
        color = "red";
      } else if (offset - assumedGCD > 100) {
        color = "yellow";
      } else {
        color = "green";
      }

      timestamp = (
        <span>
          {formatTimestamp(event.timestamp)}{" "}
          <span className={color}>
            (+{formatTimestamp(event.gcd_offset, false)})
          </span>
        </span>
      );
    }

    const formatBuff = (buff) => {
      return (
        <img
          key={buff.abilityGameID}
          src={buff.ability_icon}
          title={buff.ability}
          alt={buff.ability}
          width={20}
        />
      );
    };

    let procsUsed = [];
    event.buffs.forEach((buff) => {
      if (event.consumes_km && buff.ability === "Killing Machine") {
        procsUsed.push(buff);
      }
      if (event.consumes_rime && buff.ability === "Rime") {
        procsUsed.push(buff);
      }
    });

    return (
      <tr className={rowClass} key={i}>
        <td className={"timestamp"}>{timestamp}</td>
        <td className={abilityTdClass}>
          <div className={abilityDivClass}>
            {icon}{" "}
            <span className={getAbilityTypeClass(event.ability_type)}>
              {ability}
            </span>
          </div>
        </td>
        <td>
          <div className={"runic-power"}>{runicPower}</div>
        </td>
        <td>
          <div className={"blood-charges"}>{bloodCharges}</div>
        </td>
        {showRunes ? (
          <>
            <td>
              <div className={"runes"}>
                {event.runes_before.map(formatRune)}
              </div>
              {event.modifies_runes && (
                <div className={"runes"}>{event.runes.map(formatRune)}</div>
              )}
            </td>
          </>
        ) : null}
        <td>
          <div className={"buffs"}>{event.buffs.map(formatBuff)}</div>
        </td>
        <td>
          <div className={"debuffs"}>{(event.debuffs || []).map(formatBuff)}</div>
        </td>
        {showProcs &&
          <td>
            <div className={"procs-used"}>{procsUsed.map(formatBuff)}</div>
          </td>
        }
      </tr>
    );
  }, []);

  const formatGCDLatency = useCallback((gcdLatency, infoOnly) => {
    const averageLatency = gcdLatency.average_latency;

    let color = "green";

    if (infoOnly) {
      color = "hl"
    } else if (averageLatency > 300) {
      color = "red";
    } else if (averageLatency > 200) {
      color = "yellow";
    }

    return (
      <div className={"gcd-latency"}>
        <i className="fa fa-clock-o hl" aria-hidden="true"></i>
        Your average GCD delay was{" "}
        <span className={color}>{averageLatency.toFixed(2)} ms</span>
      </div>
    );
  }, []);
  const formatDiseases = useCallback((diseasesDropped) => {
    const numDiseasesDropped = diseasesDropped.num_diseases_dropped;

    if (numDiseasesDropped > 0) {
      return (
        <div className={"diseases-dropped"}>
          <i className="fa fa-times red" aria-hidden="true"></i>
          You dropped diseases{" "}
          <span className={"hl"}>{numDiseasesDropped}</span> times on boss
          targets
        </div>
      );
    } else {
      return (
        <div className={"diseases-dropped"}>
          <i className="fa fa-check green" aria-hidden="true"></i>
          Nice work, you didn't drop diseases on boss targets before the last 10
          seconds of the fight!
        </div>
      );
    }
  }, []);

  const formatFlask = useCallback((flaskUsage) => {
    const hasFlask = flaskUsage.has_flask;

    if (hasFlask) {
      return (
        <div className={"flask-usage"}>
          <i className="fa fa-check green" aria-hidden="true"></i>
          You had a Flask (Winter's Bite or Falling Leaves)
        </div>
      );
    }
    return (
      <div className={"flask-usage"}>
        <i className="fa fa-times red" aria-hidden="true"></i>
        You did not have a Flask (Winter's Bite or Falling Leaves)
      </div>
    );
  }, []);

  const formatFood = useCallback((foodUsage) => {
    const hasFood = foodUsage.has_food;

    if (hasFood) {
      return (
        <div className={"food-usage"}>
          <i className="fa fa-check green" aria-hidden="true"></i>
          You had Food Buff (+300 STR)
        </div>
      );
    }
    return (
      <div className={"food-usage"}>
        <i className="fa fa-times red" aria-hidden="true"></i>
        You did not have Food Buff (+300 STR)
      </div>
    );
  }, []);

  const formatKillingMachineSpeed = useCallback((killingMachine) => {
    const totalTimeSeconds = killingMachine.total_time_seconds || 0;

    return (
      <div className={"killing-machine-speed"}>
        <i className="fa fa-hourglass-half hl" aria-hidden="true"></i>
        Total time to use KM procs across fight:{" "}
        <span className={"hl"}>
          {totalTimeSeconds.toFixed(1)} seconds
        </span>
      </div>
    );
  }, []);

  const formatKillingMachineRotation = useCallback((killingMachine) => {
    const averageLatency = killingMachine.avg_latency || 0;
    const averageLatencySeconds = killingMachine.avg_time_seconds || (averageLatency / 1000);
    const numUsed = killingMachine.num_used;
    const numTotal = killingMachine.num_total;
    let color = "green";

    if (averageLatencySeconds > 2.5) {
      color = "red";
    } else if (averageLatencySeconds > 2.0) {
      color = "yellow";
    }

    return (
      <div className={"killing-machine-rotation"}>
        <i className="fa fa-clock-o hl" aria-hidden="true"></i>
        You used{" "}
        <span className={"hl"}>
          {numUsed} of {numTotal}
        </span>{" "}
        Killing Machine procs with an average delay of{" "}
        <span className={color}>
          {averageLatencySeconds.toFixed(2)} seconds
        </span>
      </div>
    );
  }, []);

  const formatKillingMachineBreakdown = useCallback((killingMachine) => {
    const kmOnFS = killingMachine.km_on_frost_strike || 0;
    const kmOnObliterate = killingMachine.km_on_obliterate || 0;
    const fsPercentage = killingMachine.frost_strike_percentage || 0;
    const totalKMUsed = kmOnFS + kmOnObliterate;

    if (totalKMUsed === 0) {
      return null; // Don't show if no KM procs were used
    }

    let icon;
    let color;
    if (fsPercentage >= 0.9) {
      icon = <i className="fa fa-check green" aria-hidden="true"></i>;
      color = "green";
    } else if (fsPercentage >= 0.8) {
      icon = <i className="fa fa-warning yellow" aria-hidden="true"></i>;
      color = "yellow";
    } else {
      icon = <i className="fa fa-times red" aria-hidden="true"></i>;
      color = "red";
    }

    return (
      <div className={"km-breakdown"}>
        {icon}
        KM procs used on Frost Strike:{" "}
        <span className={color}>
          {kmOnFS} of {totalKMUsed} ({(fsPercentage * 100).toFixed(1)}%)
        </span>
        {kmOnObliterate > 0 && (
          <span className={"hl"}>, Obliterate: {kmOnObliterate}</span>
        )}
      </div>
    );
  }, []);

  const formatObliterateDuringRime = useCallback((obliterateDuringRime) => {
    const badUsages = obliterateDuringRime.bad_usages;
    const totalObliterates = obliterateDuringRime.total_obliterates;

    if (badUsages === 0) {
      return (
        <div className={"obliterate-rime-usage"}>
          <i className="fa fa-check-circle hl green" aria-hidden="true"></i>
          You never used Obliterate during Rime procs{" "}
          <span className={"green"}>(0 bad usages)</span>
        </div>
      );
    } else {
      return (
        <div className={"obliterate-rime-usage"}>
          <i className="fa fa-times red" aria-hidden="true"></i>
          You used Obliterate during Rime procs{" "}
          <span className={"red"}>
            {badUsages} time{badUsages > 1 ? 's' : ''}
          </span>
          {totalObliterates > 0 && (
            <span className={"hl"}> (out of {totalObliterates} total Obliterates)</span>
          )}
        </div>
      );
    }
  }, []);

  const formatObliterateDeathRuneUsage = useCallback((obliterateDeathRune) => {
    const badUsages = obliterateDeathRune.bad_usages;
    const totalObliterates = obliterateDeathRune.total_obliterates;

    if (badUsages === 0) {
      return (
        <div className={"obliterate-death-rune-usage"}>
          <i className="fa fa-check-circle hl green" aria-hidden="true"></i>
          You always used optimal rune combinations for Obliterate{" "}
          <span className={"green"}>(0 suboptimal usages)</span>
        </div>
      );
    } else {
      return (
        <div className={"obliterate-death-rune-usage"}>
          <i className="fa fa-times red" aria-hidden="true"></i>
          You used suboptimal rune combinations for Obliterate{" "}
          <span className={"red"}>
            {badUsages} time{badUsages > 1 ? 's' : ''}
          </span>
          {totalObliterates > 0 && (
            <span className={"hl"}> (out of {totalObliterates} total Obliterates)</span>
          )}
        </div>
      );
    }
  }, []);

  const formatPillarOfFrostUsage = useCallback((pillarUsage) => {
    const numUsed = pillarUsage.num_used;
    const possibleUsages = pillarUsage.possible_usages;
    const usagePercentage = pillarUsage.usage_percentage;

    let icon;
    let colorClass;

    if (usagePercentage >= 1.0) {
      icon = <i className="fa fa-check green" aria-hidden="true"></i>;
      colorClass = "green";
    } else if (usagePercentage >= 0.9) {
      icon = <i className="fa fa-warning yellow" aria-hidden="true"></i>;
      colorClass = "yellow";
    } else {
      icon = <i className="fa fa-times red" aria-hidden="true"></i>;
      colorClass = "red";
    }

    return (
      <div className={"pillar-of-frost-usage"}>
        {icon}
        You used Pillar of Frost{" "}
        <span className={colorClass}>
          {numUsed} out of {possibleUsages} possible times
        </span>
        <span className={"hl"}> ({(usagePercentage * 100).toFixed(0)}%)</span>
      </div>
    );
  }, []);

  const formatPlagueStrikeDeathRuneUsage = useCallback((plagueStrikeDeathRune) => {
    const badUsages = plagueStrikeDeathRune.bad_usages;
    const totalPlagueStrikes = plagueStrikeDeathRune.total_plague_strikes;

    if (badUsages === 0) {
      return (
        <div className={"plague-strike-death-rune-usage"}>
          <i className="fa fa-check green" aria-hidden="true"></i>
          You never used Plague Strike with Death runes{" "}
          <span className={"green"}>(0 bad usages)</span>
        </div>
      );
    } else {
      return (
        <div className={"plague-strike-death-rune-usage"}>
          <i className="fa fa-times red" aria-hidden="true"></i>
          You used Plague Strike with Death runes{" "}
          <span className={"red"}>
            {badUsages} time{badUsages > 1 ? 's' : ''}
          </span>
          {totalPlagueStrikes > 0 && (
            <span className={"hl"}> (out of {totalPlagueStrikes} total Plague Strikes)</span>
          )}
        </div>
      );
    }
  }, []);

  const formatEmpoweredRuneWeapon = useCallback((erw) => {
    const numUsages = erw.num_usages;
    const totalRunesWasted = erw.total_runes_wasted;
    const totalRpWasted = erw.total_rp_wasted;
    const avgRunesWasted = erw.average_runes_wasted;
    const avgRpWasted = erw.average_rp_wasted;

    if (numUsages === 0) {
      return (
        <div className={"empowered-rune-weapon"}>
          <i className="fa fa-info-circle hl" aria-hidden="true"></i>
          No Empowered Rune Weapon usages detected
        </div>
      );
    }

    let runeIcon, rpIcon;
    let runeColor, rpColor;

    // Color coding for efficiency
    if (avgRunesWasted <= 1) {
      runeIcon = <i className="fa fa-check green" aria-hidden="true"></i>;
      runeColor = "green";
    } else if (avgRunesWasted <= 2) {
      runeIcon = <i className="fa fa-warning yellow" aria-hidden="true"></i>;
      runeColor = "yellow";
    } else {
      runeIcon = <i className="fa fa-times red" aria-hidden="true"></i>;
      runeColor = "red";
    }

    if (avgRpWasted <= 5) {
      rpIcon = <i className="fa fa-check green" aria-hidden="true"></i>;
      rpColor = "green";
    } else if (avgRpWasted <= 15) {
      rpIcon = <i className="fa fa-warning yellow" aria-hidden="true"></i>;
      rpColor = "yellow";
    } else {
      rpIcon = <i className="fa fa-times red" aria-hidden="true"></i>;
      rpColor = "red";
    }

    return (
      <div className={"empowered-rune-weapon"}>
        <div>
          {runeIcon}
          Empowered Rune Weapon runes wasted:{" "}
          <span className={runeColor}>
            {totalRunesWasted} total
          </span>
          <span className={"hl"}> ({avgRunesWasted.toFixed(1)} avg per usage)</span>
        </div>
        <div>
          {rpIcon}
          Empowered Rune Weapon RP wasted:{" "}
          <span className={rpColor}>
            {totalRpWasted} total
          </span>
          <span className={"hl"}> ({avgRpWasted.toFixed(1)} avg per usage)</span>
        </div>
      </div>
    );
  }, []);

  const formatHowlingBlast = useCallback((howlingBlast) => {
    const numBadUsages = howlingBlast.num_bad_usages;

    if (numBadUsages === 0) {
      return (
        <div className={"howling-blast"}>
          <i className="fa fa-check green" aria-hidden="true"></i>
          You always used Howling Blast with Rime or on 3+ targets
        </div>
      );
    }
    return (
      <div className={"howling-blast"}>
        <i className="fa fa-times red" aria-hidden="true"></i>
        You used Howling Blast <span className={"hl"}>{numBadUsages}</span>{" "}
        times without Rime or on less than 3 targets
      </div>
    );
  }, []);

  const formatPotions = useCallback((potions) => {
    const potionsUsed = potions.potions_used;
    const total = potionsUsed > 2 ? potionsUsed : 2

    if (potionsUsed >= 2) {
      return (
        <div className={"potions"}>
          <i className="fa fa-check green" aria-hidden="true"></i>
          You used <span className={"hl"}>{potionsUsed} of {total}</span> Potions (Mogu Power)
        </div>
      );
    }
    return (
      <div className={"potions"}>
        <i className="fa fa-times red" aria-hidden="true"></i>
        You used <span className={"hl"}>{potionsUsed} of 2</span> Potions (Mogu Power)
      </div>
    );
  }, []);

  const formatUA = useCallback((UA) => {
    const numActual = UA.num_actual;
    const numPossible = UA.num_possible;
    const windows = UA.windows;

    const formatWindows = () => {
      return (
        <div className={"windows"}>
          {windows.map((window, i) => {
            let icon = <i className="fa fa-times red" aria-hidden="true" />;
            if (window.num_actual === window.num_possible) {
              icon = <i className="fa fa-check green" aria-hidden="true" />;
            }

            return (
              <div key={i} className={"window"}>
                {icon}
                Hit{" "}
                <span className={"hl"}>
                  {window.num_actual} of {window.num_possible}
                </span>{" "}
                Obliterates {window.with_erw ? "(with ERW) " : ""}
              </div>
            );
          })}
        </div>
      );
    };

    let icon = <i className="fa fa-times red" aria-hidden="true" />;
    if (numActual === numPossible) {
      icon = <i className="fa fa-check green" aria-hidden="true" />;
    }
    return (
      <div className={"unbreakable-armor-analysis"}>
        {icon}
        You used Unbreakable Armor{" "}
        <span className={"hl"}>
          {numActual} of {numPossible}
        </span>{" "}
        possible times. Within those windows:
        {formatWindows()}
      </div>
    );
  }, []);

  const formatRunicPower = useCallback((runicPower) => {
    const overcapTimes = runicPower.overcap_times
    const overcapSum = runicPower.overcap_sum
    const gainedSum = runicPower.gained_sum

    return (
      <div className={"runic-power-analysis"}>
        <div>
          <i className="fa fa-info hl" aria-hidden="true"></i>
          You gained a total of <span className={"hl"}>{gainedSum}</span> Runic Power using AMS
        </div>
        <div>
          <i className="fa fa-info hl" aria-hidden="true"></i>
          You over-capped Runic Power <span className={"hl"}>
            {overcapTimes}
          </span>{" "}
          times for a total of
          <span className={"hl"}> {overcapSum} RP</span> wasted
        </div>
      </div>
    );
  }, []);

  const formatRime = useCallback(rime => {
    const numTotal = rime.num_total
    const numUsed = rime.num_used
    return (
      <div className={"rime-analysis"}>
        <i className="fa fa-info hl" aria-hidden="true"></i>
        You used your Rime procs <span className={"hl"}>
          {numUsed} of {numTotal}
        </span>{" "}
        times
      </div>
    )
  }, [])

  const formatFesteringStrikeWaste = useCallback(festeringStrikeWaste => {
    const oneDeathRune = festeringStrikeWaste.one_death_rune_casts
    const twoDeathRune = festeringStrikeWaste.two_death_rune_casts
    const totalWasted = festeringStrikeWaste.total_death_runes_wasted

    const icon = <i className="fa fa-info hl" aria-hidden="true"></i>

    return (
      <div className={"festering-strike-waste"}>
        {icon}
        Festering Strike wasted <span className={"hl"}>{totalWasted}</span> death runes
        {totalWasted > 0 && (
          <span> (<span className={"hl"}>{oneDeathRune}</span> × 1DR, <span className={"hl"}>{twoDeathRune}</span> × 2DR)</span>
        )}
      </div>
    )
  }, [])

  const formatBloodChargeCaps = useCallback(bloodChargeCaps => {
    if (!bloodChargeCaps.has_blood_tap_talent) {
      return null // Don't show if player doesn't have Blood Tap talent
    }

    const totalCaps = bloodChargeCaps.total_caps
    const totalWasted = bloodChargeCaps.total_charges_wasted
    let icon = <i className="fa fa-check green" aria-hidden="true"></i>
    if (totalCaps > 5) {
      icon = <i className="fa fa-times red" aria-hidden="true"></i>
    } else if (totalCaps > 2) {
      icon = <i className="fa fa-warning yellow" aria-hidden="true"></i>
    }

    return (
      <div className={"blood-charge-caps"}>
        {icon}
        Exceeded blood charge cap: <span className={"hl"}>{totalCaps}</span> times ({totalWasted} charges wasted)
      </div>
    )
  }, [])

  const formatScore = useCallback(score => {
    let color = "red"
    if (score > 0.8) {
      color = "green"
    } else if (score > 0.65) {
      color = "yellow"
    } else if (score > 0.5) {
      color = "orange"
    }

    return (
      <h2>
        Analysis score: <span className={`total-score ${color}`}>{(score * 100).toFixed(2)}</span>
        <span className={"total-score-tooltip"}>
          <Tooltip tooltipText="A score of how well you did on this fight, based upon Speed, Rotation and Misc. metrics, each weighted differently. Range is 0-100."/>
        </span>
      </h2>
    )
  }, [])

  if (analysis.isLoading || analysis.error) {
    return;
  }

  const data = analysis.data;
  const fight = data.fight_metadata;
  const events = data.events;

  let fightRanking, playerRanking, dps
  if (Object.keys(fight.rankings).length !== 0) {
    fightRanking = fight.rankings.fight_ranking?.speed_percentile || "n/a"
    playerRanking = fight.rankings.player_ranking?.rank_percentile || "n/a"
    dps = Math.round(fight.rankings.player_ranking?.dps) || "n/a"
  } else {
    fightRanking = "n/a"
    playerRanking = "n/a"
    dps = "n/a"
  }
  const summary = data.analysis;
  const isUnholy = data.spec === "Frost"

  return (
    <div className={"analysis-summary"}>
    <div className="summary-data">
    {/*<h3>Summary Data</h3>
          <pre>{JSON.stringify(summary, null, 2)}</pre>*/}
        </div>

      <div className={"fight-summary"}>
        <h2>{fight.source}</h2>
        <div className={"summary-line"}>
          Encounter: <span className={"hl"}>{fight.encounter}</span>
        </div>
        <div className={"summary-line"}>
          DPS:{" "}
          <span className={"hl"}>
            {dps}
          </span>{" "}
          ({formatRanking(playerRanking)})
        </div>
        <div className={"summary-line"}>
          Duration:{" "}
          <span className={"hl"}>{formatTimestamp(fight.duration)}</span> (
          {formatRanking(fightRanking)})
        </div>
      </div>
      <div className={"total-score-div"}>
        {formatScore(summary.analysis_scores.total_score)}
      </div>

      <Tabs defaultTab={0}>
        <Tab label="Rotation" icon={<i className="fa fa-cogs" />}>
          <div className="fight-analysis">
            <div className="analysis-section">
              <h3>Speed</h3>
              {formatGCDLatency(summary.gcd_latency, isUnholy)}
              {summary.killing_machine && formatKillingMachineSpeed(summary.killing_machine)}
            </div>

            <div className="analysis-section">
              <h3>Rotation</h3>
              {summary.killing_machine && formatKillingMachineRotation(summary.killing_machine)}
              {summary.killing_machine && formatKillingMachineBreakdown(summary.killing_machine)}
              {summary.obliterate_during_rime && formatObliterateDuringRime(summary.obliterate_during_rime)}
              {summary.obliterate_death_rune_usage && formatObliterateDeathRuneUsage(summary.obliterate_death_rune_usage)}
              {summary.plague_strike_death_rune_usage && formatPlagueStrikeDeathRuneUsage(summary.plague_strike_death_rune_usage)}
              {summary.pillar_of_frost_usage && formatPillarOfFrostUsage(summary.pillar_of_frost_usage)}
              {summary.empowered_rune_weapon && formatEmpoweredRuneWeapon(summary.empowered_rune_weapon)}
              {summary.dnd !== undefined && formatUpTime(summary.dnd.uptime, "Death and Decay", false, summary.dnd.max_uptime)}
              {summary.dark_transformation_uptime !== undefined && formatUpTime(summary.dark_transformation_uptime, "Dark Transformation", false, summary.dark_transformation_max_uptime)}
              {summary.melee_uptime !== undefined && formatUpTime(summary.melee_uptime, "Melee")}
              {summary.unbreakable_armor && formatUA(summary.unbreakable_armor)}
              {summary.blood_plague_uptime !== undefined && formatUpTime(summary.blood_plague_uptime, "Blood Plague")}
              {summary.frost_fever_uptime !== undefined && formatUpTime(summary.frost_fever_uptime, "Frost Fever")}
              {summary.unholy_presence_uptime !== undefined && formatUpTime(summary.unholy_presence_uptime, "Unholy Presence")}
              {summary.blood_charge_caps && formatBloodChargeCaps(summary.blood_charge_caps)}
              {summary.festering_strike_waste && formatFesteringStrikeWaste(summary.festering_strike_waste)}
              {summary.diseases_dropped && formatDiseases(summary.diseases_dropped)}
              {summary.howling_blast_bad_usages && formatHowlingBlast(summary.howling_blast_bad_usages)}
              {summary.runic_power && formatRunicPower(summary.runic_power)}
              {summary.rime && formatRime(summary.rime)}
            </div>

            {summary.soul_reaper && (
              <div className="analysis-section">
                <SoulReaperAnalysis soulReaper={summary.soul_reaper} />
              </div>
            )}

            {summary.outbreak_snapshots && (
              <div className="analysis-section">
                <OutbreakAnalysis outbreak_snapshots={summary.outbreak_snapshots} />
              </div>
            )}


            <div className="analysis-section">
              <h3>Miscellaneous</h3>
              {summary.trinket_usages && summary.trinket_usages.map((trinket, index) => (
                <div key={index}>
                  {formatUsage(
                    trinket.num_actual,
                    trinket.num_possible,
                    <>{formatIcon(trinket.name, trinket.icon)} {trinket.name}</>,
                  )}
                </div>
              ))}
              {summary.synapse_springs && formatUsage(
                summary.synapse_springs.num_actual,
                summary.synapse_springs.num_possible,
                "Synapse Springs",
              )}
              {summary.potion_usage && formatPotions(summary.potion_usage)}
              {summary.flask_usage && formatFlask(summary.flask_usage)}
              {summary.food_usage && formatFood(summary.food_usage)}
            </div>
          </div>
        </Tab>

        <Tab label="Pets" icon={<i className="fa fa-paw" />}>
          <div className="fight-analysis">
            {summary.ghoul && (
              <div className="analysis-section">
                <GhoulAnalysis ghoul={summary.ghoul} />
              </div>
            )}
            {summary.raise_dead && (
              <div className="analysis-section">
                <RaiseDeadAnalysis raise_dead={summary.raise_dead} />
              </div>
            )}
            {summary.dark_transformation && (
              <div className="analysis-section">
                <DarkTransformationAnalysis dark_transformation={summary.dark_transformation} />
              </div>
            )}
            {summary.gargoyle && (
              <div className="analysis-section">
                <GargoyleAnalysis gargoyle={summary.gargoyle} />
              </div>
            )}
            {summary.army && (
              <div className="analysis-section">
                <ArmyAnalysis army={summary.army} />
              </div>
            )}
            {summary.army_dynamic && (
              <div className="analysis-section">
                <ArmyDynamicAnalysis army_dynamic={summary.army_dynamic} />
              </div>
            )}
          </div>
        </Tab>

        <Tab label="Timeline" icon={<i className="fa fa-clock-o" />}>
          <div className="fight-analysis">
            <div className={"events-table"}>
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Ability</th>
                    <th>RP</th>
                    <th>BC</th>
                    {summary.has_rune_spend_error ? null : (
                      <>
                        <th>Runes</th>
                      </>
                    )}
                    <th>Buffs</th>
                    <th>Debuffs</th>
                    {data.show_procs && <th>Procs Used</th>}
                  </tr>
                </thead>
                <tbody>
                  {events.map((event, i) =>
                    formatEvent(event, !summary.has_rune_spend_error, data.show_procs, i)
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </Tab>
      </Tabs>
    </div>
  );
};

export const Analysis = () => {
  return <Summary />
}
