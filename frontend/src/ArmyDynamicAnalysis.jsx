import {formatIcon, formatTimestamp, formatUpTime, formatUsage, hl, Info} from "./helpers"


export const ArmyDynamicAnalysis = ({ army_dynamic }) => {
  const { windows } = army_dynamic

  return (
    <div>
      <h3>Army of the Dead</h3>
      <div>
        {formatUsage(army_dynamic.num_actual, army_dynamic.num_possible, "Army of the Dead")}
        <div className="windows">
          {windows.length === 0 && army_dynamic.num_actual === 0 ? (
            <div className="no-windows">
              <i className="fa fa-info-circle hl" aria-hidden="true"></i>
              No Army of the Dead casts detected. Cast Army of the Dead to see detailed buff analysis during army windows. If Army was cast before the fight started, it will not be detected here.
            </div>
          ) : null}
          {windows.map((window, i) => {
            const numAttacks = window.num_attacks

            return (
              <div className="army-window" key={i}>
                <div className="army-subheader">
                  <b>Army {i+1}:</b> ({hl(formatTimestamp(window.start))} - {hl(formatTimestamp(window.end))})
                </div>
                <div>
                  {Info}
                  <span>Damage: {hl(window.damage.toLocaleString())} ({hl(numAttacks)} attacks)</span>
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
                {window.pillar_of_frost_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.pillar_of_frost_uptime, "Pillar of Frost")}
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
