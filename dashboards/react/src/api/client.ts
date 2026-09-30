import type {
  GoalAnalysisRow,
  HomeAwayRow,
  LeagueTableRow,
  PipelineHealth,
  ProgressionRow,
  Season,
  Team,
} from './types'

// Empty by default: the Vite dev server proxies /api to the local backend
// (see vite.config.ts). In production, set VITE_API_BASE_URL to the
// deployed backend's origin (e.g. https://football-analytics-api.onrender.com).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`)
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
