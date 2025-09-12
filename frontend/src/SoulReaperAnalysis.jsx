import {formatTimestamp, hl, Info, Check, Warning, X} from "./helpers"

export const SoulReaperAnalysis = ({ soulReaper }) => {
  if (!soulReaper.execute_phase_detected) {
    return (
      <div>
        <h3>Soul Reaper</h3>
        <div>
          {Info}
          <span>No execute phase detected (boss never reached 35% HP)</span>
        </div>
      </div>
    )
  }

  const efficiency = (soulReaper.execute_phase_casts / Math.max(1, soulReaper.max_possible_casts)) * 100
  const efficiencyColor = efficiency >= 90 ? "green" : efficiency >= 75 ? "yellow" : "red"
  const efficiencyIcon = efficiency >= 90 ? Check : efficiency >= 75 ? Warning : X
  
  const firstCastColor = soulReaper.first_cast_delay !== null 
    ? (soulReaper.first_cast_delay <= 2 ? "green" : "yellow") 
    : "red"
  const firstCastIcon = soulReaper.first_cast_delay !== null 
    ? (soulReaper.first_cast_delay <= 2 ? Check : Warning) 
    : X

  return (
    <div>
      <h3>Soul Reaper (Execute Phase)</h3>
      <div>
        {Info}
        <span>Execute phase started at {hl(formatTimestamp(soulReaper.execute_phase_start))} (35% boss HP)</span>
      </div>
      <div>
        {Info}
        <span>Execute phase duration: {hl(soulReaper.execute_phase_duration.toFixed(1))}s</span>
      </div>
      <div>
        {efficiencyIcon}
        <span>
          Soul Reaper casts: {hl(soulReaper.execute_phase_casts)} of {hl(soulReaper.max_possible_casts)} possible
          {" "}(<span className={efficiencyColor}>{efficiency.toFixed(1)}%</span> efficiency)
        </span>
      </div>
      {soulReaper.first_cast_delay !== null ? (
        <div>
          {firstCastIcon}
          <span>
            First cast delay: <span className={firstCastColor}>{soulReaper.first_cast_delay.toFixed(1)}s</span>
            {soulReaper.first_cast_delay <= 2 ? " (Good!)" : " (Should cast within 2s of 35%)"}
          </span>
        </div>
      ) : (
        <div>
          {firstCastIcon}
          <span className="red">No Soul Reaper casts detected in execute phase!</span>
        </div>
      )}
      <div>
        {Info}
        <span>Total Soul Reaper casts: {hl(soulReaper.total_casts)}</span>
      </div>
    </div>
  )
}