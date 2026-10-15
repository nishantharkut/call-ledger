import { Button, Group } from '@mantine/core'
import styles from './LedgerTable.module.css'

export function MatchActions({ match, payment, onAction, disabled, pending }) {
  // Reviewed matches stay visible, but only active proposals have action buttons.
  if (
    match.status !== 'proposed' ||
    !['suggested', 'needs_review'].includes(payment.status)
  ) {
    return null
  }

  return (
    <Group gap={8} wrap="nowrap">
      {['approve', 'reject'].map((action) => (
        <Button
          key={action}
          size="xs"
          variant={action === 'approve' ? 'filled' : 'outline'}
          className={styles.actionButton}
          color={action === 'approve' ? '#247448' : '#b23b3b'}
          disabled={disabled}
          loading={pending?.action === action && pending.id === match.id}
          aria-label={`${action === 'approve' ? 'Approve' : 'Reject'} ${match.line_item.expected_reference} for ${payment.bank_reference}`}
          onClick={() => onAction(action, match.id, payment.id)}
        >
          {action === 'approve' ? 'Approve' : 'Reject'}
        </Button>
      ))}
    </Group>
  )
}
