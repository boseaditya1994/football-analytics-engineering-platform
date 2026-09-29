interface Props {
  form: string // JSON array string like ["WIN","DRAW","LOSS"]
}

export function FormPills({ form }: Props) {
  let results: string[] = []
  try {
    results = JSON.parse(form)
  } catch {
    results = []
  }
  return (
    <div className="form-pills">
      {results.map((r, i) => (
        <span key={i} className={`form-pill ${r}`} title={r}>
          {r === 'WIN' ? 'W' : r === 'DRAW' ? 'D' : 'L'}
        </span>
      ))}
    </div>
  )
}
