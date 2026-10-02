import { useEffect, useMemo, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import { CompetitionPicker } from '../components/CompetitionPicker'
import { SeasonPicker } from '../components/SeasonPicker'
import type { ProgressionRow, Team } from '../api/types'
import { useCompetitions } from '../hooks/useCompetitions'
import { useSeasons } from '../hooks/useSeasons'

const PALETTE = ['#7c5cff', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899']

export function Progression() {
  const { competitions, competition, setCompetition, loading: competitionsLoading } =
    useCompetitions()
  const { seasons, season, setSeason, loading: seasonsLoading } = useSeasons(competition)
  const [teams, setTeams] = useState<Team[]>([])
  const [selectedTeamIds, setSelectedTeamIds] = useState<number[]>([])
  const [rows, setRows] = useState<ProgressionRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!competition || !season) return
    api.teams(competition, season).then(setTeams)
    // Team selection doesn't carry over across competitions/seasons a team didn't play in.
    setSelectedTeamIds([])
  }, [competition, season])

  useEffect(() => {
    if (!season) return
    setLoading(true)
    api
      .progression(competition, season, selectedTeamIds.length ? selectedTeamIds : undefined)
      .then(setRows)
      .finally(() => setLoading(false))
  }, [competition, season, selectedTeamIds])

  const chartData = useMemo(() => {
    const byMatchweek = new Map<number, Record<string, number | string>>()
    for (const row of rows) {
      const existing = byMatchweek.get(row.matchweek) ?? { matchweek: row.matchweek }
      existing[row.team_name] = row.league_position
      byMatchweek.set(row.matchweek, existing)
    }
    return [...byMatchweek.values()].sort(
      (a, b) => (a.matchweek as number) - (b.matchweek as number),
    )
  }, [rows])

  const teamNamesInChart = useMemo(
    () => [...new Set(rows.map((r) => r.team_name))],
    [rows],
  )

  const maxPosition = teams.length || 20

  function toggleTeam(teamId: number) {
    setSelectedTeamIds((prev) =>
      prev.includes(teamId) ? prev.filter((id) => id !== teamId) : [...prev, teamId],
    )
  }

  if (competitionsLoading || seasonsLoading) return <div className="state-msg">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1>League Table Progression</h1>
        <div className="controls">
          <CompetitionPicker
            competitions={competitions}
            value={competition}
            onChange={setCompetition}
          />
          <SeasonPicker seasons={seasons} value={season} onChange={setSeason} />
        </div>
      </div>

      <div className="panel">
        <h2>Select teams to compare (defaults to all {teams.length} if none selected)</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {teams.map((t) => (
            <button
              key={t.team_id}
              className={selectedTeamIds.includes(t.team_id) ? 'active' : ''}
              onClick={() => toggleTeam(t.team_id)}
            >
              {t.team_short_name}
            </button>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2>Position by Matchweek</h2>
        {loading ? (
          <div className="state-msg">Loading progression...</div>
        ) : (
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262b36" />
              <XAxis
                dataKey="matchweek"
                stroke="#9aa1ae"
                label={{ value: 'Matchweek', position: 'insideBottom', offset: -2, fill: '#9aa1ae' }}
              />
              <YAxis
                reversed
                domain={[1, maxPosition]}
                stroke="#9aa1ae"
                allowDecimals={false}
                label={{ value: 'Position', angle: -90, position: 'insideLeft', fill: '#9aa1ae' }}
              />
              <Tooltip
                contentStyle={{ background: '#171a21', border: '1px solid #262b36', borderRadius: 8 }}
              />
              <Legend />
              {teamNamesInChart.map((name, i) => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={PALETTE[i % PALETTE.length]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
