import { Fragment, useCallback, useState } from 'react'
import { Button, Stack, Table, Text } from '@mantine/core'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { formatDate, formatMoney } from '../utils/format'
import { MatchActions } from './MatchActions'
import { MatchCandidates } from './MatchCandidates'
import { StatusBadge } from './StatusBadge'
import styles from './LedgerTable.module.css'

export function TransactionRow({ payment, onAction, disabled, pending, feedback }) {
  const [expanded, setExpanded] = useState(false)

  // Debits and finalized credits remain in the table without review controls.
  const active =
    payment.type === 'credit' && ['suggested', 'needs_review'].includes(payment.status)
  const single = payment.matches.length === 1 ? payment.matches[0] : null
  const multiple = payment.matches.length > 1
  const ToggleIcon = expanded ? ChevronDown : ChevronRight

  const revealCandidates = useCallback((row) => {
    if (!row) {
      return
    }

    const container = row.closest('[role="region"]')
    const heading = container.querySelector(':scope > table > thead')
    const paymentRow = row.previousElementSibling

    // Reveal candidates below the sticky heading without changing horizontal scroll.
    container.scrollTop +=
      paymentRow.getBoundingClientRect().top -
      container.getBoundingClientRect().top -
      heading.offsetHeight -
      8
  }, [])

  return (
    <Fragment>
      <Table.Tr>
        <Table.Td className={styles.date}>{formatDate(payment.date)}</Table.Td>
        <Table.Td className={styles.description}>
          <span className={styles.bankDescription}>{payment.description}</span>
          <span className={styles.reference}>Bank ref: {payment.bank_reference}</span>
        </Table.Td>
        <Table.Td className={styles.money}>{formatMoney(payment.amount)}</Table.Td>
        <Table.Td>
          <StatusBadge status={payment.status} />
        </Table.Td>
        <Table.Td className={styles.match}>
          {single && (
            <>
              <strong>{single.line_item.investor_name}</strong>
              <span className={styles.secondary}>
                Call #{single.line_item.call_number} ·{' '}
                {single.line_item.expected_reference}
              </span>
              <span className={styles.secondary}>
                Due {formatDate(single.line_item.due_date)}
              </span>
              <span className={styles.reason}>{single.reason}</span>
              {single.status === 'rejected' && <StatusBadge status="rejected" />}
            </>
          )}

          {multiple && (
            <Button
              size="compact-sm"
              variant="subtle"
              color="ledger"
              px={0}
              leftSection={<ToggleIcon size={15} aria-hidden="true" />}
              aria-expanded={expanded}
              aria-controls={`matches-${payment.id}`}
              onClick={() => setExpanded(!expanded)}
            >
              {payment.matches.length} matches
            </Button>
          )}

          {payment.review_reason && (
            <span className={styles.reason}>{payment.review_reason}</span>
          )}

          {!single && !multiple && !payment.review_reason && (
            <span className={styles.secondary}>No match</span>
          )}
        </Table.Td>
        <Table.Td className={styles.actions}>
          <Stack gap={8} align="flex-start">
            {single?.status === 'proposed' && active && (
              <MatchActions
                match={single}
                payment={payment}
                onAction={onAction}
                disabled={disabled}
                pending={pending}
              />
            )}

            {active && (
              <Button
                size="xs"
                variant="default"
                color="gray"
                disabled={disabled}
                className={styles.actionButton}
                loading={pending?.action === 'ignore' && pending.id === payment.id}
                aria-label={`Ignore ${payment.bank_reference}`}
                onClick={() => onAction('ignore', payment.id, payment.id)}
              >
                Ignore
              </Button>
            )}

            {!active && (
              <Text size="sm" c="dimmed">
                No action needed
              </Text>
            )}

            {feedback && (active || feedback.color !== 'teal') && (
              <Text
                size="xs"
                className={styles.feedback}
                data-kind={feedback.color}
                role={feedback.color === 'red' ? 'alert' : 'status'}
              >
                {feedback.text}
              </Text>
            )}
          </Stack>
        </Table.Td>
      </Table.Tr>

      {multiple && expanded && (
        <Table.Tr id={`matches-${payment.id}`} ref={revealCandidates}>
          <Table.Td colSpan={6} className={styles.expandedCell}>
            <MatchCandidates
              payment={payment}
              onAction={onAction}
              disabled={disabled}
              pending={pending}
            />
          </Table.Td>
        </Table.Tr>
      )}
    </Fragment>
  )
}
