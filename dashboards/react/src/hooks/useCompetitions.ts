import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Competition } from '../api/types'

export function useCompetitions() {
  const [competitions, setCompetitions] = useState<Competition[]>([])
  const [competition, setCompetition] = useState<string>('PL')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .competitions()
      .then(setCompetitions)
      .finally(() => setLoading(false))
  }, [])

  return { competitions, competition, setCompetition, loading }
}
