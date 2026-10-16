import { useState } from 'react'
import { Alert, Button, FileInput } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { Upload } from 'lucide-react'
import styles from './StatementUpload.module.css'
import { IMPORT_NOTIFICATION_ID } from '../utils/importFeedback'

export function StatementUpload({ upload, pending, disabled, error, clearError }) {
  const [file, setFile] = useState(null)
  const [validationError, setValidationError] = useState('')

  async function submit(event) {
    event.preventDefault()

    if (!file) {
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      const message = 'Choose a CSV file no larger than 10 MB.'
      setValidationError(message)
      notifications.hide(IMPORT_NOTIFICATION_ID)
      notifications.show({
        id: IMPORT_NOTIFICATION_ID,
        message,
        color: 'red',
        role: 'alert',
      })
      return
    }

    setValidationError('')

    // Keep the selected file available if the upload needs to be retried.
    if (await upload(file)) {
      setFile(null)
    }
  }

  return (
    <section className={styles.section} aria-labelledby="import-heading">
      <div>
        <h2 id="import-heading" className={styles.heading}>
          Import a statement
        </h2>
        <p className={styles.description}>CSV statement, UTF-8, up to 10 MB</p>
      </div>

      <form onSubmit={submit} className={styles.form}>
        <FileInput
          aria-label="Bank statement"
          placeholder="Choose a CSV file"
          accept=".csv,text/csv"
          value={file}
          onChange={(value) => {
            setFile(value)
            setValidationError('')
            // A replacement file should not inherit the previous upload's error.
            clearError()
          }}
          clearable
          disabled={disabled}
          clearButtonProps={{ 'aria-label': 'Clear selected statement' }}
          leftSection={<Upload size={16} aria-hidden="true" />}
          className={styles.file}
        />
        <Button
          type="submit"
          disabled={!file || disabled}
          loading={pending}
          className={styles.submit}
        >
          {pending ? 'Importing' : 'Import statement'}
        </Button>
      </form>

      {(validationError || error) && (
        <Alert
          color="red"
          title="Import could not be completed"
          role="alert"
          className={styles.error}
        >
          {validationError || error}
        </Alert>
      )}
    </section>
  )
}
