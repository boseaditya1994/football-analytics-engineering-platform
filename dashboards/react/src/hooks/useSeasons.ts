import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Season } from '../api/types'

export function useSeasons() {
  const [seasons, setSeasons] = useState<Season[]>([])
  const [season, setSeason] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .seasons()
      .then((rows) => {
        setSeasons(rows)
        if (rows.length > 0) setSeason(rows[0].season)
      })
      .finally(() => setLoading(false))
  }, [])

  return { seasons, season, setSeason, loading }
}

export function seasonLabel(season: string): string {
  const start = Number(season)
  return `${start}/${String(start + 1).slice(2)}`
}
