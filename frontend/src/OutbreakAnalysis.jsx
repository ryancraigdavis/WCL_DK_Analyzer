import {formatTimestamp, hl, Info, Check, X} from "./helpers"


export const OutbreakAnalysis = ({ outbreak_snapshots }) => {
  const { snapshots } = outbreak_snapshots

  const formatBuffSnapshot = (buffActive, buffName, hasThisBuff, isOrc = false) => {
    // Don't show Blood Fury for non-orcs
    if (buffName === "Blood Fury" && !isOrc) {
      return null
    }

    // Don't show buffs that the player doesn't have
    if (!hasThisBuff) {
      return null
    }

    const icon = buffActive ? Check : X
    const text = buffActive ? "You snapshotted" : "You did not snapshot"

    return (
      <div key={buffName}>
        {icon}
        <span> {text} {buffName}</span>
      </div>
    )
  }

  if (!snapshots || snapshots.length === 0) {
    return (
      <div>
        <h3>Outbreak</h3>
        <div>
          {Info}
          <span>No Outbreak casts detected in this fight</span>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h3>Outbreak</h3>
      <div className="windows">
        {snapshots.map((snapshot, i) => {
          return (
            <div key={i}>
              <div className="outbreak-window">
                <div className="outbreak-subheader">
                  <b>Outbreak {i+1}:</b> ({hl(formatTimestamp(snapshot.timestamp))})
                </div>
                {formatBuffSnapshot(snapshot.synapse_springs, "Synapse Springs", snapshot.has_synapse_springs, snapshot.is_orc)}
                {formatBuffSnapshot(snapshot.potion_of_mogu_power, "Potion of Mogu Power", snapshot.has_potion, snapshot.is_orc)}
                {formatBuffSnapshot(snapshot.fallen_crusader, "Fallen Crusader", snapshot.has_fallen_crusader, snapshot.is_orc)}
                {formatBuffSnapshot(snapshot.lei_shen_final_orders, "Lei Shen's Final Orders", snapshot.has_lei_shen_final_orders, snapshot.is_orc)}
                {formatBuffSnapshot(snapshot.relic_of_xuen, "Relic of Xuen", snapshot.has_relic_of_xuen, snapshot.is_orc)}
                {formatBuffSnapshot(snapshot.blood_fury, "Blood Fury", snapshot.has_blood_fury, snapshot.is_orc)}
              </div>
              {i < snapshots.length - 1 && <br />}
            </div>
          )
        })}
      </div>
    </div>
  )
}