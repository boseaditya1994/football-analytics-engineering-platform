import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { PipelineHealth as PipelineHealthData } from '../api/types'

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

export function PipelineHealth() {
  const [data, setData] = useState<PipelineHealthData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .pipelineHealth()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="state-msg">Loading pipeline health...</div>
  if (!data) return <div className="state-msg">No pipeline data available.</div>

  const { summary, data_quality, recent_runs } = data
  const successRate =
    summary.total_runs > 0
      ? ((summary.successful_runs / summary.total_runs) * 100).toFixed(1)
      : '-'

  return (
    <div>
      <div className="page-header">
        <h1>Data Pipeline Health</h1>
      </div>

      <div className="kpi-row">
        <div className="kpi-card">
          <div className="label">Last Successful Run</div>
          <div className="value" style={{ fontSize: '1.1rem' }}>
            {formatDate(summary.last_success_at)}
          </div>
        </div>
        <div className="kpi-card">
          <div className="label">Total Runs</div>
          <div className="value">{summary.total_runs}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Success Rate</div>
          <div className="value">{successRate}%</div>
        </div>
        <div className="kpi-card">
          <div className="label">Failed Runs</div>
          <div className="value">{summary.failed_runs}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Records Loaded</div>
          <div className="value">{summary.total_records_inserted ?? 0}</div>
        </div>
        <div className="kpi-card">
          <div className="label">DQ Checks Failed</div>
          <div className="value">{data_quality.failed_checks ?? 0}</div>
        </div>
      </div>

      <div className="panel">
        <h2>Recent Pipeline Runs</h2>
        <table>
          <thead>
            <tr>
              <th>Started</th>
              <th>Pipeline</th>
              <th>Dataset</th>
              <th>Season</th>
              <th>Status</th>
              <th>Received</th>
              <th>Inserted</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {recent_runs.map((run) => (
              <tr key={run.run_id}>
                <td>{formatDate(run.started_at)}</td>
                <td>{run.pipeline_name}</td>
                <td>{run.dataset}</td>
                <td>{run.season ?? '-'}</td>
                <td>
                  <span className={`status-pill ${run.status}`}>{run.status}</span>
                </td>
                <td>{run.records_received ?? '-'}</td>
                <td>{run.records_inserted ?? '-'}</td>
                <td style={{ maxWidth: 260, whiteSpace: 'normal', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {run.error_message ?? ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
