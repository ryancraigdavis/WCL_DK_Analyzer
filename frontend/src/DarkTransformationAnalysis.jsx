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
                  <span>Damage: {hl(window.damage.toLocaleString())} ({hl(numAttacks)} attacks</span>
                </div>
                {window.trinket_uptimes.map((uptime, i) => {
                  const icon = formatIcon(uptime.name, uptime.icon)

                  return (
                    <div key={i}>
                      {formatUpTime(uptime.uptime, <>{icon} {uptime.name}</>)}
                    </div>
                  )
                })}
                <div>
                  {formatUpTime(window.bloodlust_uptime, "Bloodlust")}
                </div>
                {window.berserking_uptime !== null && (
                  <div>
                    {formatUpTime(window.berserking_uptime, "Berserking")}
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
