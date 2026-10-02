import type {
  Competition,
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
  competitions: () => get<Competition[]>('/api/competitions'),
  seasons: (competition: string) =>
    get<Season[]>(`/api/seasons?competition=${encodeURIComponent(competition)}`),
  teams: (competition: string, season?: string) => {
    const qs = season ? `&season=${encodeURIComponent(season)}` : ''
    return get<Team[]>(`/api/teams?competition=${encodeURIComponent(competition)}${qs}`)
  },
  leagueTable: (competition: string, season: string) =>
    get<LeagueTableRow[]>(
      `/api/league-table?competition=${encodeURIComponent(competition)}&season=${encodeURIComponent(season)}`,
    ),
  progression: (competition: string, season: string, teamIds?: number[]) => {
    const qs = teamIds?.length ? `&team_ids=${teamIds.join(',')}` : ''
    return get<ProgressionRow[]>(
      `/api/progression?competition=${encodeURIComponent(competition)}&season=${encodeURIComponent(season)}${qs}`,
    )
  },
  homeAway: (competition: string, season: string) =>
    get<HomeAwayRow[]>(
      `/api/home-away?competition=${encodeURIComponent(competition)}&season=${encodeURIComponent(season)}`,
    ),
  goalAnalysis: (competition: string, season: string) =>
    get<GoalAnalysisRow[]>(
      `/api/goal-analysis?competition=${encodeURIComponent(competition)}&season=${encodeURIComponent(season)}`,
    ),
  pipelineHealth: () => get<PipelineHealth>('/api/pipeline-health'),
}
