import { useState } from "react"
import type { MemoryHit } from "@/api/chat"

function relativeTime(value: string) {
  const timestamp = new Date(value).getTime()
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000))
  if (seconds < 60) return "just now"
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export default function MemoryInspector({
  memories,
  label,
}: {
  memories: MemoryHit[]
  label?: string
}) {
  const [open, setOpen] = useState(false)
  const defaultLabel = `Answered using ${memories.length} ${memories.length === 1 ? "memory" : "memories"} from your history`

  return (
    <div className="memory-inspector">
      <button
        type="button"
        className="memory-toggle"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span>🧠 {label || defaultLabel}</span>
        <span>{open ? "−" : "+"}</span>
      </button>
      {open && <div className="memory-list">
        {memories.map((memory) => {
          const similarity = memory.similarity == null ? null : Math.max(0, Math.min(1, memory.similarity))
          return <article className="memory-hit" key={memory.id}>
            <div className="memory-hit-header">
              <span className={`memory-type memory-type-${memory.memory_type}`}>{memory.memory_type}</span>
              <span>{relativeTime(memory.created_at)}</span>
            </div>
            <p>{memory.content}</p>
            <div className="memory-metrics">
              <span>Similarity {similarity == null ? "n/a" : `${Math.round(similarity * 100)}%`}</span>
              <span>Importance {Math.round(memory.importance * 100)}%</span>
            </div>
            {similarity != null && <div className="memory-score"><span style={{ width: `${similarity * 100}%` }} /></div>}
          </article>
        })}
      </div>}
    </div>
  )
}
