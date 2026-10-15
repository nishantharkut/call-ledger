import { useState } from 'react'
import { importStatement } from '../api/reconciliation'

export function useStatementImport(organization, refresh) {
  const [summary, setSummary] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')

  async function upload(file) {
    setPending(true)
    setError('')
    setSummary(null)

    try {
      const result = await importStatement(organization, file)
      setSummary({ ...result, filename: file.name })

      // The import succeeded even if fetching its updated rows fails afterward.
      await refresh(1)

      return true
    } catch (failure) {
      setError(failure.message)
      return false
    } finally {
      setPending(false)
    }
  }

  return { upload, summary, pending, error }
}
