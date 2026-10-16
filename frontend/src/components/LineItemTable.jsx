import { Table } from '@mantine/core'
import { DISPLAY_CURRENCY, formatDate, formatMoney } from '../utils/format'
import { RequestFeedback } from './RequestFeedback'
import { StatusBadge } from './StatusBadge'
import { TableSkeleton } from './TableSkeleton'
import styles from './LedgerTable.module.css'

export function LineItemTable({ state, onRetry, disabled }) {
  // Funding balances and statuses come from the API rather than local calculations.
  return (
    <section id="capital-calls" aria-labelledby="calls-heading" aria-busy={state.loading}>
      <div className={styles.sectionHeading}>
        <h2 id="calls-heading">Capital calls</h2>
        {state.data && (
          <span className={styles.count}>
            {state.data.length} line {state.data.length === 1 ? 'item' : 'items'} ·{' '}
            {DISPLAY_CURRENCY}
          </span>
        )}
      </div>

      <RequestFeedback
        {...state}
        loading={state.loading && Boolean(state.data)}
        onRetry={onRetry}
        disabled={disabled}
      />

      {!state.data && state.loading && !state.error && (
        <TableSkeleton label="Loading capital calls" columns={7} />
      )}

      {state.data?.length > 0 && (
        <p className={styles.scrollHint}>
          Scroll horizontally to see funding and balances.
        </p>
      )}

      {state.data?.length > 0 && (
        <div className={styles.surface}>
          <div
            className={styles.scroll}
            role="region"
            aria-label="Capital calls table"
            tabIndex={0}
          >
            <Table
              className={`${styles.table} ${styles.lineItems}`}
              verticalSpacing="sm"
              horizontalSpacing="md"
            >
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Investor</Table.Th>
                  <Table.Th>Call</Table.Th>
                  <Table.Th>Reference</Table.Th>
                  {['Called', 'Funded', 'Remaining'].map((label) => (
                    <Table.Th key={label} className={styles.money}>
                      {label}
                    </Table.Th>
                  ))}
                  <Table.Th>Status</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {state.data.map((item) => (
                  <Table.Tr key={item.id}>
                    <Table.Td>
                      <strong>{item.investor_name}</strong>
                    </Table.Td>
                    <Table.Td>
                      <span title={`Issued ${formatDate(item.call_date)}`}>
                        Call #{item.call_number}
                      </span>
                      <span className={styles.secondary}>
                        Due {formatDate(item.due_date)}
                      </span>
                    </Table.Td>
                    <Table.Td className={styles.code}>{item.expected_reference}</Table.Td>
                    {['amount_called', 'amount_funded', 'amount_remaining'].map(
                      (field) => (
                        <Table.Td key={field} className={styles.money}>
                          {formatMoney(item[field])}
                        </Table.Td>
                      ),
                    )}
                    <Table.Td>
                      <StatusBadge status={item.status} />
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </div>
        </div>
      )}

      {state.data?.length === 0 && !state.loading && !state.error && (
        <div className={styles.empty}>
          <h3>No capital call line items</h3>
          <p>This organization has no capital calls to reconcile.</p>
        </div>
      )}
    </section>
  )
}
