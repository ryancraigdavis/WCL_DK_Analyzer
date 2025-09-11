import {formatIcon, formatTimestamp, formatUsage, hl, Info} from "./helpers"


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
                  const gargoyleDuration = window.end - window.start
                  const uptimePercent = gargoyleDuration > 0 ? ((snapshot.uptime / gargoyleDuration) * 100).toFixed(1) : 0

                  return (
                    <div key={i}>
                      {Info}
                      <span>{icon} {snapshot.name}: {hl(`${uptimePercent}%`)} uptime</span>
                    </div>
                  )
                })}
                <div>
                  {Info}
                  <span>Synapse Springs: {hl(`${window.synapse_springs_uptime > 0 ? (((window.synapse_springs_uptime || 0) / (window.end - window.start)) * 100).toFixed(1) : 0}%`)} uptime</span>
                </div>
                <div>
                  {Info}
                  <span>Potion of Mogu Power: {hl(`${window.potion_uptime > 0 ? (((window.potion_uptime || 0) / (window.end - window.start)) * 100).toFixed(1) : 0}%`)} uptime</span>
                </div>
                <div>
                  {Info}
                  <span>Fallen Crusader: {hl(`${window.fallen_crusader_uptime > 0 ? (((window.fallen_crusader_uptime || 0) / (window.end - window.start)) * 100).toFixed(1) : 0}%`)} uptime</span>
                </div>
                {window.snapshotted_bloodfury !== null && (
                  <div>
                    {Info}
                    <span>Blood Fury: {hl(`${window.bloodfury_uptime > 0 ? (((window.bloodfury_uptime || 0) / (window.end - window.start)) * 100).toFixed(1) : 0}%`)} uptime</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
