import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Season } from '../api/types'

export function useSeasons(competition: string) {
  const [seasons, setSeasons] = useState<Season[]>([])
  const [season, setSeason] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!competition) return
    setLoading(true)
    api
      .seasons(competition)
      .then((rows) => {
        setSeasons(rows)
        setSeason(rows.length > 0 ? rows[0].season : '')
      })
      .finally(() => setLoading(false))
  }, [competition])

  return { seasons, season, setSeason, loading }
}

export function seasonLabel(season: string): string {
  const start = Number(season)
  return `${start}/${String(start + 1).slice(2)}`
}
