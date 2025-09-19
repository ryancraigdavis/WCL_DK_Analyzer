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

  const efficiency = (soulReaper.execute_window_hits / Math.max(1, soulReaper.max_possible_hits)) * 100
  const efficiencyColor = efficiency >= 80 ? "green" : efficiency >= 60 ? "yellow" : "red"
  const efficiencyIcon = efficiency >= 80 ? Check : efficiency >= 60 ? Warning : X

  const firstHitColor = soulReaper.first_hit_delay !== null
    ? (soulReaper.first_hit_delay <= 3 ? "green" : "yellow")
    : "red"
  const firstHitIcon = soulReaper.first_hit_delay !== null
    ? (soulReaper.first_hit_delay <= 3 ? Check : Warning)
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
          Soul Reaper hits in execute window: {hl(soulReaper.execute_window_hits)} of {hl(soulReaper.max_possible_hits)} possible
          {" "}(<span className={efficiencyColor}>{efficiency.toFixed(1)}%</span> efficiency)
        </span>
      </div>
      {soulReaper.first_hit_delay !== null ? (
        <div>
          {firstHitIcon}
          <span>
            First execute hit delay: <span className={firstHitColor}>{soulReaper.first_hit_delay.toFixed(1)}s</span>
            {soulReaper.first_hit_delay <= 3 ? " (Good!)" : " (Should hit within 3s of 35%)"}
          </span>
        </div>
      ) : (
        <div>
          {firstHitIcon}
          <span className="red">No Soul Reaper hits detected in execute window!</span>
        </div>
      )}
      <div>
        {Info}
        <span>Total Soul Reaper hits: {hl(soulReaper.total_hits)}</span>
      </div>
    </div>
  )
}