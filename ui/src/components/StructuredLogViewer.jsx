import { useState, useRef, useEffect, useCallback } from 'react'

/* ─── Tool type icons (small, monochrome SVGs) ─── */
const ToolIcons = {
  shell: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
      <path d="M2.5 4l4 3-4 3V4zm5.5 6h5v1H8V10z" />
    </svg>
  ),
  read_file: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
      <path d="M4 1h5.5L13 4.5V14a1 1 0 01-1 1H4a1 1 0 01-1-1V2a1 1 0 011-1zm5 1H4v12h8V5H9V2zM5 8h6v1H5V8zm0 2h4v1H5v-1z" />
    </svg>
  ),
  write_file: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
      <path d="M11.5 1.3l3.2 3.2-8 8H3.5v-3.2l8-8zm-1 2.4L4.5 9.7v1.8h1.8l6-6-1.8-1.8z" />
    </svg>
  ),
  default: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
      <path d="M8 1a7 7 0 100 14A7 7 0 008 1zM7 5h2v1H7V5zm0 2h2v4H7V7z" />
    </svg>
  ),
}

function getToolIcon(name) {
  const base = name.split('__').pop() || name
  return ToolIcons[base] || ToolIcons.default
}

function getToolLabel(name) {
  // Strip any "prefix__" to get the bare tool name, then humanize
  const base = name.split('__').pop() || name
  return base.replace(/_/g, ' ')
}

function getToolArgSummary(args) {
  if (args?.command) return args.command
  if (args?.path) return args.path
  // Generic: show first string value
  const first = Object.values(args || {}).find((v) => typeof v === 'string')
  return first || null
}

/* ─── Text message block ─── */
function TextMessage({ text }) {
  return (
    <div className="py-2.5">
      <p className="text-[13px] text-slate-200 leading-[1.7] whitespace-pre-wrap">
        {text}
      </p>
    </div>
  )
}

/* ─── Collapsible tool call card ─── */
function ToolCall({ call, result, notifications }) {
  const [expanded, setExpanded] = useState(false)
  const contentRef = useRef(null)
  const isError = result?.status === 'error'
  const isPending = !result
  const label = getToolLabel(call.name)
  const icon = getToolIcon(call.name)
  const argSummary = getToolArgSummary(call.arguments)

  return (
    <div className="my-1.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className={`
          w-full flex items-center gap-2.5 pl-3 pr-3.5 py-2 rounded-md text-left
          transition-colors duration-150 group
          ${isError
            ? 'bg-red-950/40 hover:bg-red-950/60'
            : 'bg-slate-800/60 hover:bg-slate-800'
          }
        `}
      >
        {/* Chevron */}
        <svg
          className={`w-3 h-3 text-slate-500 shrink-0 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
          viewBox="0 0 16 16" fill="currentColor"
        >
          <path d="M6 3l5 5-5 5V3z" />
        </svg>

        {/* Tool icon + label */}
        <span className={`shrink-0 ${isError ? 'text-red-400/70' : 'text-slate-500'}`}>
          {icon}
        </span>
        <span className={`text-xs font-medium shrink-0 ${isError ? 'text-red-400/80' : 'text-slate-400'}`}>
          {label}
        </span>

        {/* Argument summary */}
        {argSummary && (
          <code className={`text-xs font-mono truncate min-w-0 ${
            isError ? 'text-red-300/60' : 'text-teal-400/80'
          }`}>
            {argSummary.length > 72 ? argSummary.slice(0, 72) + '\u2026' : argSummary}
          </code>
        )}

        {/* Status badge */}
        <span className="ml-auto shrink-0">
          {isPending ? (
            <span className="inline-flex items-center gap-1.5 text-xs text-teal-400">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal-400"></span>
              </span>
              running
            </span>
          ) : isError ? (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-red-400">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              error
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs text-emerald-500/80 group-hover:text-emerald-400 transition-colors">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          )}
        </span>
      </button>

      {/* Expandable output area */}
      <div
        ref={contentRef}
        className={`overflow-hidden transition-all duration-200 ease-in-out ${
          expanded ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className={`mx-0.5 rounded-b-md border-x border-b px-3 py-2.5 space-y-1.5 ${
          isError
            ? 'border-red-900/40 bg-red-950/20'
            : 'border-slate-800 bg-slate-850/50'
        }`}
          style={{ backgroundColor: isError ? undefined : 'rgb(17 24 33)' }}
        >
          {/* Notifications (log lines from in-progress execution) */}
          {notifications.length > 0 && (
            <div className="space-y-px">
              {notifications.map((n, i) => (
                <div key={i} className="text-[11px] leading-relaxed text-slate-600 font-mono select-text">
                  {n.message}
                </div>
              ))}
            </div>
          )}

          {/* Tool result output */}
          {result && (
            <pre className={`text-xs font-mono whitespace-pre-wrap leading-[1.65] select-text ${
              isError ? 'text-red-300/90' : 'text-slate-300/90'
            }`}>
              {result.output}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}

/* ─── Completion banner ─── */
function CompletionBanner({ totalTokens }) {
  return (
    <div className="mt-4 pt-3 border-t border-slate-800">
      <div className="flex items-center justify-between py-1.5">
        <span className="inline-flex items-center gap-2 text-xs text-emerald-500/90 font-medium">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Run complete
        </span>
        {totalTokens != null && (
          <span className="text-[11px] text-slate-600 font-mono tabular-nums">
            {totalTokens.toLocaleString()} tokens
          </span>
        )}
      </div>
    </div>
  )
}

/* ─── Main viewer ─── */
export default function StructuredLogViewer({ events, isActive }) {
  const bottomRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events.length])

  // Group events into renderable blocks
  const blocks = buildBlocks(events)

  return (
    <div
      ref={containerRef}
      className="bg-slate-900 rounded-lg border border-slate-800 overflow-auto max-h-[700px]"
    >
      {/* Live indicator bar */}
      {isActive && (
        <div className="sticky top-0 z-10 flex items-center gap-2 px-4 py-2 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal-500"></span>
          </span>
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Live</span>
        </div>
      )}

      <div className="px-4 py-3">
        {blocks.length === 0 ? (
          <div className="text-[13px] text-slate-600 py-4">
            {isActive ? 'Waiting for output\u2026' : 'No events.'}
          </div>
        ) : (
          blocks.map((block, i) => {
            if (block.type === 'text') {
              return <TextMessage key={i} text={block.text} />
            }
            if (block.type === 'tool') {
              return (
                <ToolCall
                  key={i}
                  call={block.call}
                  result={block.result}
                  notifications={block.notifications}
                />
              )
            }
            if (block.type === 'complete') {
              return <CompletionBanner key={i} totalTokens={block.total_tokens} />
            }
            return null
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

/* ─── Event grouping logic ─── */
function buildBlocks(events) {
  const blocks = []
  const toolResults = {}
  const notifications = {}

  // Index tool results and notifications
  for (const event of events) {
    if (event.type === 'tool_call') {
      notifications[event.id] = []
    } else if (event.type === 'tool_result') {
      toolResults[event.id] = event
    } else if (event.type === 'notification') {
      const id = event.extension_id
      if (!notifications[id]) notifications[id] = []
      notifications[id].push(event)
    }
  }

  // Build ordered blocks
  for (const event of events) {
    if (event.type === 'message' && event.content_type === 'text') {
      blocks.push({ type: 'text', text: event.text, id: event.id })
    } else if (event.type === 'tool_call') {
      blocks.push({
        type: 'tool',
        call: event,
        result: toolResults[event.id] || null,
        notifications: notifications[event.id] || [],
      })
    } else if (event.type === 'complete') {
      blocks.push({ type: 'complete', total_tokens: event.total_tokens })
    }
  }

  return blocks
}
