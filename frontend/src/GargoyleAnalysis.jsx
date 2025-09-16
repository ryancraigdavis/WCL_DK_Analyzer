import {formatIcon, formatTimestamp, formatUpTime, formatUsage, hl, Info} from "./helpers"


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
                {window.trinket_snapshots
                  .filter(snapshot => snapshot.uptime !== 0)
                  .map((snapshot, i) => {
                    const icon = formatIcon(snapshot.name, snapshot.icon)
                    return (
                      <div key={i}>
                        {formatUpTime(snapshot.uptime, <>{icon} {snapshot.name}</>)}
                      </div>
                    )
                  })
                }
                <div>
                  {formatUpTime(window.fallen_crusader_uptime, "Fallen Crusader")}
                </div>
                {window.synapse_springs_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.synapse_springs_uptime, "Synapse Springs")}
                  </div>
                )}
                {window.potion_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.potion_uptime, "Potion of Mogu Power")}
                  </div>
                )}
                {window.bloodfury_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.bloodfury_uptime, "Blood Fury")}
                  </div>
                )}
                {window.berserking_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.berserking_uptime, "Berserking")}
                  </div>
                )}
                {window.bloodlust_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.bloodlust_uptime, "Bloodlust")}
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
