import type { Season } from '../api/types'
import { seasonLabel } from '../hooks/useSeasons'

interface Props {
  seasons: Season[]
  value: string
  onChange: (season: string) => void
}

export function SeasonPicker({ seasons, value, onChange }: Props) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {seasons.map((s) => (
        <option key={s.season} value={s.season}>
          {seasonLabel(s.season)}
        </option>
      ))}
    </select>
  )
}
