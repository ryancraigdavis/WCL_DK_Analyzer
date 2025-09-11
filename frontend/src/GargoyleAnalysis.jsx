import {booleanCheck, formatIcon, formatTimestamp, formatUsage, hl, Info} from "./helpers"


export const GargoyleAnalysis = ({ gargoyle }) => {
  const { windows } = gargoyle

  return (
    <div>
      <h3>Gargoyle</h3>
      <div>
        {formatUsage(gargoyle.num_actual, gargoyle.num_possible, "Gargoyle")}
        <div className="windows">
          {windows.map((window, i) => {
            const numCast = window.num_casts
            const numMelee = window.num_melees

            return (
              <div className="gargoyle-window" key={i}>
                <div className="gargoyle-subheader">
                  <b>Gargoyle {i+1}:</b> ({hl(formatTimestamp(window.start))} - {hl(formatTimestamp(window.end))})
                </div>
                <div>
                  {Info}
                  <span>Damage: {hl(window.damage.toLocaleString())} ({hl(numCast)} casts, {hl(numMelee)} melees)</span>
                </div>
                {window.trinket_snapshots.map((snapshot, i) => {
                  const icon = formatIcon(snapshot.name, snapshot.icon)

                  return (
                    <div key={i}>
                      {booleanCheck(snapshot.did_snapshot, <>You snapshotted {icon} {snapshot.name}</>, <>You did not snapshot {icon} {snapshot.name}</>)}
                    </div>
                  )
                })}
                {booleanCheck(window.snapshotted_synapse, "You snapshotted Synapse Springs", "You did not snapshot Synapse Springs")}
                {booleanCheck(window.snapshotted_potion, "You snapshotted your Potion of Mogu Power", "You did not snapshot your Potion of Mogu Power")}
                {booleanCheck(window.snapshotted_fc, "You snapshotted Fallen Crusader", "You did not snapshot Fallen Crusader")}
                {window.snapshotted_bloodfury !== null && booleanCheck(window.snapshotted_bloodfury, "You snapshotted Blood Fury", "You did not snapshot Blood Fury")}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
