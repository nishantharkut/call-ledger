import { Alert, Button, Group, Modal } from '@mantine/core'
import { ImportSummary } from './ImportSummary'
import { getImportFeedback } from '../utils/importFeedback'
import styles from './ImportSummary.module.css'

export function ImportResultDialog({ summary, opened, onClose, onExited }) {
  if (!summary) {
    return null
  }

  const feedback = getImportFeedback(summary)

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      onExitTransitionEnd={onExited}
      returnFocus={false}
      title={feedback.title}
      size="lg"
      centered
      xOffset={16}
      padding="lg"
      closeButtonProps={{ 'aria-label': 'Close import results' }}
      classNames={{ title: styles.dialogTitle, close: styles.dialogClose }}
    >
      {summary.refreshFailed && (
        <Alert color="yellow" mb="md">
          The import finished, but updated tables could not be loaded. Close this dialog
          and use Retry before reviewing payments.
        </Alert>
      )}

      <ImportSummary summary={summary} embedded />

      <Group justify="flex-end" mt="lg">
        <Button onClick={onClose} className={styles.dialogButton}>
          Close
        </Button>
      </Group>
    </Modal>
  )
}
