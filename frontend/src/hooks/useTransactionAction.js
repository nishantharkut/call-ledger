import { useState } from 'react'
import { performAction } from '../api/reconciliation'

export function useTransactionAction(organization, refresh) {
  const [pending, setPending] = useState(null)
  const [message, setMessage] = useState(null)

  async function run(action, id, paymentId) {
    setPending({ action, id, paymentId })
    setMessage(null)

    try {
      await performAction(organization, action, id)
      // Keep review controls disabled until the updated balances have been fetched.
      const refreshed = await refresh()

      const text = {
        approve: 'Match approved.',
        reject: 'Match rejected.',
        ignore: 'Transaction ignored.',
      }[action]

      setMessage({
        paymentId,
        color: refreshed ? 'teal' : 'yellow',
        text: refreshed
          ? text
          : `${text} Updated data could not be loaded. Refresh before continuing.`,
      })
    } catch (failure) {
      setMessage({ paymentId, color: 'red', text: failure.message })

      // A conflict means the proposal may be stale. Load the server's current state.
      if (failure.status === 409) {
        await refresh()
      }
    } finally {
      setPending(null)
    }
  }

  return { run, pending, message }
}
