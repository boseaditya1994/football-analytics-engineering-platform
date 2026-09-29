import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { FormPills } from '../components/FormPills'
import { SeasonPicker } from '../components/SeasonPicker'
import type { LeagueTableRow } from '../api/types'
import { useSeasons } from '../hooks/useSeasons'

export function Overview() {
  const { seasons, season, setSeason, loading: seasonsLoading } = useSeasons()
  const [table, setTable] = useState<LeagueTableRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!season) return
    setLoading(true)
    api
      .leagueTable(season)
      .then(setTable)
      .finally(() => setLoading(false))
  }, [season])

  if (seasonsLoading) return <div className="state-msg">Loading...</div>

  const matchesPlayed = table.reduce((sum, r) => sum + r.played_games, 0) / 2
  const totalGoals = table.reduce((sum, r) => sum + r.goals_for, 0)
  const leader = table[0]
  const topScorer = [...table].sort((a, b) => b.goals_for - a.goals_for)[0]

  return (
    <div>
      <div className="page-header">
        <h1>EPL Overview</h1>
        <div className="controls">
          <SeasonPicker seasons={seasons} value={season} onChange={setSeason} />
        </div>
      </div>

      {!loading && table.length > 0 && (
        <div className="kpi-row">
          <div className="kpi-card">
            <div className="label">Matches Played</div>
            <div className="value">{matchesPlayed}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Goals Scored</div>
            <div className="value">{totalGoals}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Goals / Match</div>
            <div className="value">
              {matchesPlayed > 0 ? (totalGoals / matchesPlayed).toFixed(2) : '-'}
            </div>
          </div>
          <div className="kpi-card">
            <div className="label">Current Leader</div>
            <div className="value">{leader?.team_name ?? '-'}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Highest Scoring</div>
            <div className="value">
              {topScorer?.team_name ?? '-'} ({topScorer?.goals_for ?? 0})
            </div>
          </div>
        </div>
      )}

      <div className="panel">
        <h2>League Table</h2>
        {loading ? (
          <div className="state-msg">Loading league table...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Team</th>
                <th>P</th>
                <th>W</th>
                <th>D</th>
                <th>L</th>
                <th>GF</th>
                <th>GA</th>
                <th>GD</th>
                <th>Pts</th>
                <th>PPG</th>
                <th>Form</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row) => (
                <tr key={row.team_id}>
                  <td>{row.league_position}</td>
                  <td>
                    <div className="team-cell">
                      <img src={row.team_crest_url} alt="" />
                      {row.team_name}
                    </div>
                  </td>
                  <td>{row.played_games}</td>
                  <td>{row.won}</td>
                  <td>{row.drawn}</td>
                  <td>{row.lost}</td>
                  <td>{row.goals_for}</td>
                  <td>{row.goals_against}</td>
                  <td>{row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}</td>
                  <td>
                    <strong>{row.points}</strong>
                  </td>
                  <td>{row.points_per_game}</td>
                  <td>
                    <FormPills form={row.form_last_5} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
