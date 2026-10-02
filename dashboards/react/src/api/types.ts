export interface Competition {
  competition_code: string
  competition_name: string
  area_name: string
}

export interface Season {
  season: string
  season_start_date: string
  season_end_date: string
  total_matchweeks: number
}

export interface Team {
  team_id: number
  team_name: string
  team_short_name: string
  team_tla: string
  team_crest_url: string
}

export interface LeagueTableRow {
  team_id: number
  team_name: string
  team_crest_url: string
  league_position: number
  played_games: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  points_per_game: string
  form_last_5: string
}

export interface ProgressionRow {
  team_id: number
  team_name: string
  matchweek: number
  league_position: number
  points: number
  position_change: number | null
}

export interface HomeAwayRow {
  team_id: number
  team_name: string
  home_played: number
  home_points: number
  home_ppg: string
  home_win_pct: string
  home_goal_difference: number
  away_played: number
  away_points: number
  away_ppg: string
  away_win_pct: string
  away_goal_difference: number
}

export interface GoalAnalysisRow {
  team_id: number
  team_name: string
  played: number
  goals_for: number
  goals_against: number
  goals_for_per_match: string
  goals_against_per_match: string
  clean_sheets: number
  clean_sheet_pct: string
  matches_failed_to_score: number
  failed_to_score_pct: string
}

export interface PipelineRun {
  run_id: string
  pipeline_name: string
  dataset: string
  competition_code: string | null
  season: string | null
  status: 'SUCCESS' | 'FAILED' | 'RUNNING'
  started_at: string
  completed_at: string | null
  records_received: number | null
  records_inserted: number | null
  records_rejected: number | null
  error_message: string | null
}

export interface PipelineHealth {
  recent_runs: PipelineRun[]
  summary: {
    total_runs: number
    successful_runs: number
    failed_runs: number
    total_records_inserted: number
    last_success_at: string | null
  }
  data_quality: {
    total_checks: number
    failed_checks: number | null
  }
}
