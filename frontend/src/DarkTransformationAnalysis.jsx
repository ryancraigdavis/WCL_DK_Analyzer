import {formatIcon, formatTimestamp, formatUpTime, formatUsage, hl, Info} from "./helpers"


export const DarkTransformationAnalysis = ({ dark_transformation }) => {
  const { windows } = dark_transformation

  return (
    <div>
      <h3>Dark Transformation</h3>
      <div>
        {formatUsage(dark_transformation.num_actual, dark_transformation.num_possible, "Dark Transformation")}
        <div className="windows">
          {windows.map((window, i) => {
            const numAttacks = window.num_attacks

            return (
              <div className="dark-transformation-window" key={i}>
                <div className="dark-transformation-subheader">
                  <b>Dark Transformation {i+1}:</b> ({hl(formatTimestamp(window.start))} - {hl(formatTimestamp(window.end))})
                </div>
                <div>
                  {Info}
                  <span>Damage: {hl(window.damage.toLocaleString())} ({hl(numAttacks)} attacks)</span>
                </div>
                <div>
                  {Info}
                  <span>Damage per Attack: {hl((window.damage / numAttacks).toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  }))}</span>
                </div>
                {window.trinket_uptimes
                  .filter(uptime => uptime.uptime !== 0)
                  .map((uptime, i) => {
                    const icon = formatIcon(uptime.name, uptime.icon)
                    return (
                      <div key={i}>
                        {formatUpTime(uptime.uptime, <>{icon} {uptime.name}</>)}
                      </div>
                    )
                  })
                }
                <div>
                  {formatUpTime(window.fallen_crusader_uptime, "Unholy Strength")}
                </div>
                {window.synapse_springs_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.synapse_springs_uptime, "Synapse Springs")}
                  </div>
                )}
                {window.potion_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.potion_uptime, "Golem's Strength (Potion)")}
                  </div>
                )}
                {window.unholy_frenzy_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.unholy_frenzy_uptime, "Unholy Frenzy")}
                  </div>
                )}
                {window.bloodlust_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.bloodlust_uptime, "Bloodlust")}
                  </div>
                )}
                {window.berserking_uptime !== null && window.berserking_uptime !== 0 && (
                  <div>
                    {formatUpTime(window.berserking_uptime, "Berserking (Troll)")}
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
