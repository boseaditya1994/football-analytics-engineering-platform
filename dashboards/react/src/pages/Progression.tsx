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
import { SeasonPicker } from '../components/SeasonPicker'
import type { ProgressionRow, Team } from '../api/types'
import { useSeasons } from '../hooks/useSeasons'

const PALETTE = ['#7c5cff', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899']

export function Progression() {
  const { seasons, season, setSeason, loading: seasonsLoading } = useSeasons()
  const [allTeams, setAllTeams] = useState<Team[]>([])
  const [teamIdsInSeason, setTeamIdsInSeason] = useState<Set<number>>(new Set())
  const [selectedTeamIds, setSelectedTeamIds] = useState<number[]>([])
  const [rows, setRows] = useState<ProgressionRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.teams().then(setAllTeams)
  }, [])

  useEffect(() => {
    if (!season) return
    api
      .leagueTable(season)
      .then((table) => setTeamIdsInSeason(new Set(table.map((r) => r.team_id))))
      .catch(() => setTeamIdsInSeason(new Set()))
    // Team selection doesn't carry over across seasons a team didn't play in.
    setSelectedTeamIds([])
  }, [season])

  useEffect(() => {
    if (!season) return
    setLoading(true)
    api
      .progression(season, selectedTeamIds.length ? selectedTeamIds : undefined)
      .then(setRows)
      .finally(() => setLoading(false))
  }, [season, selectedTeamIds])

  const teams = useMemo(
    () => allTeams.filter((t) => teamIdsInSeason.has(t.team_id)),
    [allTeams, teamIdsInSeason],
  )

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

  function toggleTeam(teamId: number) {
    setSelectedTeamIds((prev) =>
      prev.includes(teamId) ? prev.filter((id) => id !== teamId) : [...prev, teamId],
    )
  }

  if (seasonsLoading) return <div className="state-msg">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1>League Table Progression</h1>
        <div className="controls">
          <SeasonPicker seasons={seasons} value={season} onChange={setSeason} />
        </div>
      </div>

      <div className="panel">
        <h2>Select teams to compare (defaults to all 20 if none selected)</h2>
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
                domain={[1, 20]}
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
