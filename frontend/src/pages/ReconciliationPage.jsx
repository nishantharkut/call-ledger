import { Button } from '@mantine/core'
import { RefreshCw } from 'lucide-react'
import { WorkspaceHeader } from '../components/WorkspaceHeader'
import { StatementUpload } from '../components/StatementUpload'
import { ImportSummary } from '../components/ImportSummary'
import { TransactionTable } from '../components/TransactionTable'
import { LineItemTable } from '../components/LineItemTable'
import { useWorkspaceData } from '../hooks/useWorkspaceData'
import { useStatementImport } from '../hooks/useStatementImport'
import { useTransactionAction } from '../hooks/useTransactionAction'
import styles from './ReconciliationPage.module.css'

export function ReconciliationPage({ organization, onOrganizationChange }) {
  const workspace = useWorkspaceData(organization)
  const statement = useStatementImport(organization, workspace.changePage)
  const actions = useTransactionAction(organization, workspace.refresh)

  const mutating = statement.pending || Boolean(actions.pending)
  const refreshing = mutating || workspace.loading

  // Block reviews if either list is stale so balances and proposals stay consistent.
  const disabled =
    refreshing || Boolean(workspace.transactions.error || workspace.lineItems.error)

  return (
    <>
      <WorkspaceHeader
        organization={organization}
        onChange={onOrganizationChange}
        disabled={mutating}
      />

      <div className={styles.shell}>
        <main className={styles.main}>
          <div className={styles.intro}>
            <div>
              <h1>Bank reconciliation</h1>
            </div>
            <Button
              variant="subtle"
              color="gray"
              size="sm"
              disabled={refreshing}
              className={styles.refreshButton}
              aria-label="Refresh"
              onClick={workspace.refresh}
              leftSection={<RefreshCw size={14} aria-hidden="true" />}
            >
              <span className={styles.refreshLabel}>Refresh</span>
            </Button>
          </div>

          <StatementUpload {...statement} disabled={mutating} />
          <ImportSummary summary={statement.summary} />

          <TransactionTable
            state={workspace.transactions}
            page={workspace.page}
            onPageChange={workspace.changePage}
            onRetry={workspace.refresh}
            onAction={actions.run}
            disabled={disabled}
            pending={actions.pending}
            message={actions.message}
            retryDisabled={refreshing}
          />

          <LineItemTable
            state={workspace.lineItems}
            onRetry={workspace.refresh}
            disabled={refreshing}
          />
        </main>
      </div>
    </>
  )
}
