import {hl, Info} from "./helpers"

export const ArmyAnalysis = ({army}) => {

  return (
    <div>
      <h3>Army of the Dead</h3>
      <div>
        {Info}
        <span>Damage: {hl(army.damage.toLocaleString())}</span>
      </div>
    </div>
  )
}
