import { Pagination, Table } from '@mantine/core'
import { TransactionRow } from './TransactionRow'
import { RequestFeedback } from './RequestFeedback'
import { TableSkeleton } from './TableSkeleton'
import { DISPLAY_CURRENCY } from '../utils/format'
import styles from './LedgerTable.module.css'

// Keep this aligned with TransactionPagination.page_size on the API.
const PAGE_SIZE = 50

export function TransactionTable({
  state,
  page,
  onPageChange,
  onRetry,
  onAction,
  disabled,
  retryDisabled,
  pending,
  message,
}) {
  const data = state.data

  return (
    <section
      id="transactions"
      aria-labelledby="transactions-heading"
      aria-busy={state.loading}
    >
      <div className={styles.sectionHeading}>
        <h2 id="transactions-heading">Transactions</h2>
        {data && <span className={styles.count}>{data.count} transactions</span>}
      </div>

      <RequestFeedback
        {...state}
        loading={state.loading && Boolean(data)}
        onRetry={onRetry}
        disabled={retryDisabled}
      />

      {!data && state.loading && !state.error && (
        <TableSkeleton label="Loading transactions" columns={6} />
      )}

      {data?.results.length > 0 && (
        <p className={styles.scrollHint}>
          Scroll horizontally to see matches and actions.
        </p>
      )}

      {data && data.results.length > 0 && (
        <div className={styles.surface}>
          <div
            className={`${styles.scroll} ${styles.transactionScroll}`}
            role="region"
            aria-label="Transactions table"
            tabIndex={0}
          >
            <Table className={styles.table} verticalSpacing="sm" horizontalSpacing="md">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Date</Table.Th>
                  <Table.Th>Bank transaction</Table.Th>
                  <Table.Th className={styles.money}>
                    Amount ({DISPLAY_CURRENCY})
                  </Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Match details</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {data.results.map((payment) => (
                  <TransactionRow
                    key={payment.id}
                    payment={payment}
                    onAction={onAction}
                    disabled={disabled}
                    pending={pending}
                    feedback={message?.paymentId === payment.id ? message : null}
                  />
                ))}
              </Table.Tbody>
            </Table>
          </div>
          <div className={styles.pagination}>
            <span>
              {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, data.count)} of{' '}
              {data.count}
            </span>
            {data.count > PAGE_SIZE && (
              <Pagination
                total={Math.ceil(data.count / PAGE_SIZE)}
                value={page}
                onChange={onPageChange}
                disabled={disabled}
                size="sm"
                aria-label="Transaction pages"
                getControlProps={(control) => ({
                  'aria-label':
                    control === 'previous'
                      ? 'Previous transaction page'
                      : 'Next transaction page',
                })}
              />
            )}
          </div>
        </div>
      )}

      {data?.results.length === 0 && !state.loading && !state.error && (
        <div className={styles.empty}>
          <h3>No transactions yet</h3>
          <p>Import a bank statement to start reconciling payments.</p>
        </div>
      )}
    </section>
  )
}
