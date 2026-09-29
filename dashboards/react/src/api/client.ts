import type {
  GoalAnalysisRow,
  HomeAwayRow,
  LeagueTableRow,
  PipelineHealth,
  ProgressionRow,
  Season,
  Team,
} from './types'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    throw new Error(`Request failed (${res.status}): ${path}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  seasons: () => get<Season[]>('/api/seasons'),
  teams: () => get<Team[]>('/api/teams'),
  leagueTable: (season: string) =>
    get<LeagueTableRow[]>(`/api/league-table?season=${encodeURIComponent(season)}`),
  progression: (season: string, teamIds?: number[]) => {
    const qs = teamIds?.length
      ? `&team_ids=${teamIds.join(',')}`
      : ''
    return get<ProgressionRow[]>(`/api/progression?season=${encodeURIComponent(season)}${qs}`)
  },
  homeAway: (season: string) =>
    get<HomeAwayRow[]>(`/api/home-away?season=${encodeURIComponent(season)}`),
  goalAnalysis: (season: string) =>
    get<GoalAnalysisRow[]>(`/api/goal-analysis?season=${encodeURIComponent(season)}`),
  pipelineHealth: () => get<PipelineHealth>('/api/pipeline-health'),
}
