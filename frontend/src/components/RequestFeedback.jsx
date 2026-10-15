import { Alert, Button, Group, Loader, Text } from '@mantine/core'
import styles from './LedgerTable.module.css'

export function RequestFeedback({ loading, error, onRetry, disabled }) {
  // A refresh failure still needs a retry control when previously loaded rows remain.
  if (error) {
    return (
      <Alert color="red" title="Could not load data" role="alert" mb="md">
        <Group justify="space-between" gap="sm">
          <Text size="sm">{error}</Text>
          <Button
            className={styles.retryButton}
            variant="white"
            color="red"
            size="xs"
            onClick={onRetry}
            disabled={disabled}
          >
            Retry
          </Button>
        </Group>
      </Alert>
    )
  }

  if (loading) {
    return (
      <Group gap="xs" role="status" mb="sm">
        <Loader size="xs" />
        <Text size="sm" c="dimmed">
          Loading data
        </Text>
      </Group>
    )
  }

  return null
}
