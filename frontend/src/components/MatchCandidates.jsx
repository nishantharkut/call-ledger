import { Table } from '@mantine/core'
import { DISPLAY_CURRENCY, formatDate, formatMoney } from '../utils/format'
import { MatchActions } from './MatchActions'
import { StatusBadge } from './StatusBadge'
import styles from './LedgerTable.module.css'

export function MatchCandidates({ payment, onAction, disabled, pending }) {
  return (
    <div className={styles.candidates}>
      <div className={styles.candidateHeading}>
        <span>Matches</span>
        <span className={styles.candidateReference}>{payment.bank_reference}</span>
      </div>
      <Table className={styles.candidateTable}>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Investor / call</Table.Th>
            <Table.Th className={styles.money}>Remaining ({DISPLAY_CURRENCY})</Table.Th>
            <Table.Th>Reason</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        {/* Keep approved and rejected candidates visible as review history. */}
        <Table.Tbody>
          {payment.matches.map((match) => (
            <Table.Tr key={match.id}>
              <Table.Td>
                <strong>{match.line_item.investor_name}</strong>
                <span className={styles.secondary}>
                  Call #{match.line_item.call_number} ·{' '}
                  {match.line_item.expected_reference}
                </span>
                <span className={styles.secondary}>
                  Due {formatDate(match.line_item.due_date)}
                </span>
              </Table.Td>
              <Table.Td className={styles.money}>
                {formatMoney(match.line_item.amount_remaining)}
              </Table.Td>
              <Table.Td>
                <span className={styles.reason}>{match.reason}</span>
              </Table.Td>
              <Table.Td>
                <StatusBadge status={match.status} />
              </Table.Td>
              <Table.Td>
                <MatchActions
                  match={match}
                  payment={payment}
                  onAction={onAction}
                  disabled={disabled}
                  pending={pending}
                />
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </div>
  )
}
