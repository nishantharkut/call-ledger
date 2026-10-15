import { lazy, Suspense, useRef } from 'react'
import { Button, Text } from '@mantine/core'
import { RefreshCw } from 'lucide-react'
import { WorkspaceHeader } from '../components/WorkspaceHeader'
import { StatementUpload } from '../components/StatementUpload'
import { ImportSummary } from '../components/ImportSummary'
import { ImportDialogBoundary } from '../components/ImportDialogBoundary'
import { TransactionTable } from '../components/TransactionTable'
import { LineItemTable } from '../components/LineItemTable'
import { useWorkspaceData } from '../hooks/useWorkspaceData'
import { useStatementImport } from '../hooks/useStatementImport'
import { useTransactionAction } from '../hooks/useTransactionAction'
import styles from './ReconciliationPage.module.css'

// The results dialog is not needed for the initial workspace render.
const ImportResultDialog = lazy(() => import('../components/ImportResultDialog'))

export function ReconciliationPage({ organization, onOrganizationChange }) {
  const workspace = useWorkspaceData(organization)
  const statement = useStatementImport(organization, workspace.changePage)
  const actions = useTransactionAction(organization, workspace.refresh)
  const importDetailsButton = useRef(null)

  const mutating = statement.pending || Boolean(actions.pending)
  const refreshing = mutating || workspace.loading

  // Block reviews if either list is stale so balances and proposals stay consistent.
  const disabled =
    refreshing || Boolean(workspace.transactions.error || workspace.lineItems.error)

  function finishImportDialog() {
    statement.notifyCompletedImport()

    // The upload button becomes disabled after its file is cleared.
    importDetailsButton.current?.focus()
  }

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
          <ImportSummary
            summary={statement.summary}
            onOpen={statement.openDialog}
            detailsButtonRef={importDetailsButton}
          />

          {statement.summary && (
            <ImportDialogBoundary>
              <Suspense
                fallback={
                  <Text role="status" size="sm">
                    Opening import details
                  </Text>
                }
              >
                <ImportResultDialog
                  summary={statement.summary}
                  opened={statement.dialogOpened}
                  onClose={statement.closeDialog}
                  onExited={finishImportDialog}
                />
              </Suspense>
            </ImportDialogBoundary>
          )}

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
