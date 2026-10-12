import React from 'react'
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react'

export default function Alert({ type = 'error', message, onClose }) {
  if (!message) return null

  const isSuccess = type === 'success'
  const isInfo = type === 'info'

  const styles = isSuccess
    ? 'bg-emerald-950/50 border-emerald-800/60 text-emerald-300'
    : isInfo
    ? 'bg-indigo-950/50 border-indigo-800/60 text-indigo-300'
    : 'bg-rose-950/50 border-rose-800/60 text-rose-300'

  const Icon = isSuccess ? CheckCircle2 : isInfo ? Info : AlertCircle

  return (
    <div className={`p-4 rounded-xl border flex items-start justify-between gap-3 text-sm shadow-lg ${styles}`}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 shrink-0 mt-0.5" />
        <div>{message}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition p-1 -mr-1 -mt-1 cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
