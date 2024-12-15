import {formatIcon, formatTimestamp, formatUpTime, formatUsage, hl, CircleRight, Info} from "./helpers"

export const DarkTransformationAnalysis = ({ dark_transformation }) => {
  const { windows } = dark_transformation

  const DTFormatUpTime = (upTime, spellName, maxUptime = 1.0) => {
    const isSpecialSpell = spellName === "Bloodlust" || spellName === "Unholy Frenzy" || spellName === "Berserking (Troll)";
    
    // Use a custom render function to override just the icon
    const customRender = (icon, content) => (
      <div className="uptime centered">
        <div>{isSpecialSpell ? icon : CircleRight}</div>
        {content}
      </div>
    );

    return formatUpTime(upTime, spellName, !isSpecialSpell, maxUptime, customRender);
  };

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
                        {DTFormatUpTime(uptime.uptime, <>{icon} {uptime.name}</>)}
                      </div>
                    )
                  })
                }
                <div>
                  {DTFormatUpTime(window.fallen_crusader_uptime, "Unholy Strength")}
                </div>
                {window.synapse_springs_uptime !== 0 && (
                  <div>
                    {DTFormatUpTime(window.synapse_springs_uptime, "Synapse Springs")}
                  </div>
                )}
                {window.potion_uptime !== 0 && (
                  <div>
                    {DTFormatUpTime(window.potion_uptime, "Golem's Strength (Potion)")}
                  </div>
                )}
                {window.unholy_frenzy_uptime !== 0 && (
                  <div>
                    {DTFormatUpTime(window.unholy_frenzy_uptime, "Unholy Frenzy")}
                  </div>
                )}
                {window.bloodlust_uptime !== 0 && (
                  <div>
                    {DTFormatUpTime(window.bloodlust_uptime, "Bloodlust")}
                  </div>
                )}
                {window.berserking_uptime !== null && window.berserking_uptime !== 0 && (
                  <div>
                    {DTFormatUpTime(window.berserking_uptime, "Berserking (Troll)")}
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
