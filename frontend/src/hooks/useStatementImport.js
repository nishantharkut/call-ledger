import { useRef, useState } from 'react'
import { notifications } from '@mantine/notifications'
import { importStatement } from '../api/reconciliation'
import { getImportFeedback, IMPORT_NOTIFICATION_ID } from '../utils/importFeedback'

export function useStatementImport(organization, refresh) {
  const [summary, setSummary] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const [dialogOpened, setDialogOpened] = useState(false)
  const completedFeedback = useRef(null)

  function clearError() {
    setError('')
    notifications.hide(IMPORT_NOTIFICATION_ID)
  }

  function notifyCompletedImport() {
    if (completedFeedback.current) {
      notifications.show(completedFeedback.current)
      completedFeedback.current = null
    }
  }

  function openDialog() {
    notifications.hide(IMPORT_NOTIFICATION_ID)
    setDialogOpened(true)
  }

  async function upload(file) {
    setPending(true)
    clearError()
    setSummary(null)
    setDialogOpened(false)
    completedFeedback.current = null

    try {
      const result = await importStatement(organization, file)

      // The import succeeded even if fetching its updated rows fails afterward.
      const refreshed = await refresh(1)
      setSummary({ ...result, filename: file.name, refreshFailed: !refreshed })
      setDialogOpened(true)

      const feedback = getImportFeedback(result)
      // Wait until the dialog exits so the toast cannot cover its controls on mobile.
      completedFeedback.current = {
        id: IMPORT_NOTIFICATION_ID,
        color: refreshed ? feedback.color : 'yellow',
        message: refreshed
          ? feedback.message
          : 'Tables could not refresh. Use Retry before reviewing.',
      }

      return true
    } catch (failure) {
      setError(failure.message)
      notifications.show({
        id: IMPORT_NOTIFICATION_ID,
        message: failure.message,
        color: 'red',
        role: 'alert',
        autoClose: 8000,
      })
      return false
    } finally {
      setPending(false)
    }
  }

  return {
    upload,
    summary,
    pending,
    error,
    clearError,
    dialogOpened,
    openDialog,
    closeDialog: () => setDialogOpened(false),
    notifyCompletedImport,
  }
}
