import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { CompetitionPicker } from '../components/CompetitionPicker'
import { SeasonPicker } from '../components/SeasonPicker'
import type { GoalAnalysisRow, HomeAwayRow, LeagueTableRow, Team } from '../api/types'
import { useCompetitions } from '../hooks/useCompetitions'
import { useSeasons } from '../hooks/useSeasons'

interface TeamStats {
  table?: LeagueTableRow
  homeAway?: HomeAwayRow
  goals?: GoalAnalysisRow
}

function StatRow({ label, a, b }: { label: string; a: string | number; b: string | number }) {
  return (
    <>
      <div className="compare-stat">
        <span>{a}</span>
        <span className="stat-label">{label}</span>
      </div>
      <div className="compare-stat">
        <span className="stat-label">{label}</span>
        <span>{b}</span>
      </div>
    </>
  )
}

export function TeamCompare() {
  const { competitions, competition, setCompetition, loading: competitionsLoading } =
    useCompetitions()
  const { seasons, season, setSeason, loading: seasonsLoading } = useSeasons(competition)
  const [teams, setTeams] = useState<Team[]>([])
  const [teamAId, setTeamAId] = useState<number | null>(null)
  const [teamBId, setTeamBId] = useState<number | null>(null)
  const [statsA, setStatsA] = useState<TeamStats>({})
  const [statsB, setStatsB] = useState<TeamStats>({})

  useEffect(() => {
    if (!competition || !season) return
    api.teams(competition, season).then((rows) => {
      setTeams(rows)
      if (rows.length >= 2) {
        setTeamAId(rows[0].team_id)
        setTeamBId(rows[1].team_id)
      }
    })
  }, [competition, season])

  useEffect(() => {
    if (!season) return
    Promise.all([
      api.leagueTable(competition, season),
      api.homeAway(competition, season),
      api.goalAnalysis(competition, season),
    ]).then(([table, homeAway, goals]) => {
      const build = (teamId: number | null): TeamStats => ({
        table: table.find((r) => r.team_id === teamId),
        homeAway: homeAway.find((r) => r.team_id === teamId),
        goals: goals.find((r) => r.team_id === teamId),
      })
      setStatsA(build(teamAId))
      setStatsB(build(teamBId))
    })
  }, [competition, season, teamAId, teamBId])

  if (competitionsLoading || seasonsLoading) return <div className="state-msg">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Team Comparison</h1>
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
        <div className="team-compare-grid">
          <select value={teamAId ?? ''} onChange={(e) => setTeamAId(Number(e.target.value))}>
            {teams.map((t) => (
              <option key={t.team_id} value={t.team_id}>
                {t.team_name}
              </option>
            ))}
          </select>
          <select value={teamBId ?? ''} onChange={(e) => setTeamBId(Number(e.target.value))}>
            {teams.map((t) => (
              <option key={t.team_id} value={t.team_id}>
                {t.team_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="panel">
        <h2>League Position</h2>
        <div className="team-compare-grid">
          <StatRow
            label="Position"
            a={statsA.table?.league_position ?? '-'}
            b={statsB.table?.league_position ?? '-'}
          />
          <StatRow label="Points" a={statsA.table?.points ?? '-'} b={statsB.table?.points ?? '-'} />
          <StatRow
            label="Points / Game"
            a={statsA.table?.points_per_game ?? '-'}
            b={statsB.table?.points_per_game ?? '-'}
          />
          <StatRow
            label="Goal Difference"
            a={statsA.table?.goal_difference ?? '-'}
            b={statsB.table?.goal_difference ?? '-'}
          />
        </div>
      </div>

      <div className="panel">
        <h2>Home / Away</h2>
        <div className="team-compare-grid">
          <StatRow
            label="Home PPG"
            a={statsA.homeAway?.home_ppg ?? '-'}
            b={statsB.homeAway?.home_ppg ?? '-'}
          />
          <StatRow
            label="Away PPG"
            a={statsA.homeAway?.away_ppg ?? '-'}
            b={statsB.homeAway?.away_ppg ?? '-'}
          />
          <StatRow
            label="Home Win %"
            a={statsA.homeAway?.home_win_pct ?? '-'}
            b={statsB.homeAway?.home_win_pct ?? '-'}
          />
          <StatRow
            label="Away Win %"
            a={statsA.homeAway?.away_win_pct ?? '-'}
            b={statsB.homeAway?.away_win_pct ?? '-'}
          />
        </div>
      </div>

      <div className="panel">
        <h2>Goals</h2>
        <div className="team-compare-grid">
          <StatRow
            label="Goals For"
            a={statsA.goals?.goals_for ?? '-'}
            b={statsB.goals?.goals_for ?? '-'}
          />
          <StatRow
            label="Goals Against"
            a={statsA.goals?.goals_against ?? '-'}
            b={statsB.goals?.goals_against ?? '-'}
          />
          <StatRow
            label="Clean Sheet %"
            a={statsA.goals?.clean_sheet_pct ?? '-'}
            b={statsB.goals?.clean_sheet_pct ?? '-'}
          />
          <StatRow
            label="Failed to Score %"
            a={statsA.goals?.failed_to_score_pct ?? '-'}
            b={statsB.goals?.failed_to_score_pct ?? '-'}
          />
        </div>
      </div>
    </div>
  )
}
