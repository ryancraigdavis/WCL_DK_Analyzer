import {booleanCheck, formatUpTime, hl, Info} from "./helpers"

export const GhoulAnalysis = ({ghoul}) => {
  return (
    <div>
      <h3>Ghoul</h3>
      <div>
        {Info}
        <span>Damage: {hl(ghoul.damage.toLocaleString())}</span>
      </div>
      {formatUpTime(ghoul.melee_uptime, "Melee")}
      {formatUpTime(ghoul.uptime, "Alive")}
      {booleanCheck(ghoul.num_claws > 0, "Your Ghoul used Claw or Sweeping Claws", `Your Ghoul did NOT use Claw or Sweeping Claws`)}
      {booleanCheck(ghoul.num_gnaws === 0, "You did not use Gnaw", `You used Gnaw ${ghoul.num_gnaws} times`)}
    </div>
  )
}
