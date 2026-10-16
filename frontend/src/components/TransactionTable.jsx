import { NativeSelect, Pagination, Table } from '@mantine/core'
import { TransactionRow } from './TransactionRow'
import { RequestFeedback } from './RequestFeedback'
import { TableSkeleton } from './TableSkeleton'
import { TransactionControls } from './TransactionControls'
import { DISPLAY_CURRENCY } from '../utils/format'
import styles from './LedgerTable.module.css'

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
  list,
  controlsDisabled,
}) {
  const data = state.data
  // Keep the range aligned with visible rows while a new page size loads.
  const loadedPageSize = state.pageSize

  return (
    <section
      id="transactions"
      aria-labelledby="transactions-heading"
      aria-busy={state.loading}
    >
      <div className={styles.sectionHeading}>
        <h2 id="transactions-heading">Transactions</h2>
        {data && (
          <span className={styles.count}>
            {data.count} {data.count === 1 ? 'transaction' : 'transactions'}
          </span>
        )}
      </div>

      <TransactionControls
        list={list}
        disabled={controlsDisabled}
        loading={state.loading && Boolean(data)}
      />

      <RequestFeedback error={state.error} onRetry={onRetry} disabled={retryDisabled} />

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
            <div className={styles.pageDetails}>
              <span>
                {(page - 1) * loadedPageSize + 1}–
                {Math.min(page * loadedPageSize, data.count)} of {data.count}
              </span>
              <NativeSelect
                label="Rows per page"
                value={String(list.pageSize)}
                onChange={(event) => list.setPageSize(Number(event.currentTarget.value))}
                data={['50', '100', '500']}
                disabled={controlsDisabled}
                size="xs"
                className={styles.pageSize}
              />
            </div>
            {data.count > loadedPageSize && (
              <Pagination
                total={Math.ceil(data.count / loadedPageSize)}
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
          <h3>{list.filtered ? 'No transactions found' : 'No transactions yet'}</h3>
          <p>
            {list.filtered
              ? 'Try another search or clear the filters.'
              : 'Import a bank statement to start reconciling payments.'}
          </p>
        </div>
      )}
    </section>
  )
}
