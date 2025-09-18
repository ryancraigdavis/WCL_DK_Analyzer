import {formatIcon, formatTimestamp, formatUpTime, formatUsage, hl, Info} from "./helpers"


export const RaiseDeadAnalysis = ({ raise_dead }) => {
  const { windows } = raise_dead

  return (
    <div>
      <h3>Raise Dead (Frost Ghoul)</h3>
      <div>
        {formatUsage(raise_dead.num_actual, raise_dead.num_possible, "Raise Dead")}
        <div className="windows">
          {windows.length === 0 && raise_dead.num_actual === 0 ? (
            <div className="no-windows">
              <i className="fa fa-info-circle hl" aria-hidden="true"></i>
              No Raise Dead casts detected. Cast Raise Dead to see detailed buff analysis during ghoul windows.
            </div>
          ) : null}
          {windows.map((window, i) => {
            const numAttacks = window.num_attacks

            return (
              <div className="raise-dead-window" key={i}>
                <div className="raise-dead-subheader">
                  <b>Ghoul {i+1}:</b> ({hl(formatTimestamp(window.start))} - {hl(formatTimestamp(window.end))})
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