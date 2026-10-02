import type { Competition } from '../api/types'

interface Props {
  competitions: Competition[]
  value: string
  onChange: (competition: string) => void
}

export function CompetitionPicker({ competitions, value, onChange }: Props) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {competitions.map((c) => (
        <option key={c.competition_code} value={c.competition_code}>
          {c.competition_name}
        </option>
      ))}
    </select>
  )
}
