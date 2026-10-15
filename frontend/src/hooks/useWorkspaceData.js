import { useCallback, useEffect, useRef, useState } from 'react'
import { getLineItems, getTransactions } from '../api/reconciliation'

const initial = { data: null, loading: true, error: '' }

function updateListState(result, setState) {
  if (result.status === 'fulfilled') {
    setState({ data: result.value, loading: false, error: '' })
    return
  }

  // Keep the last loaded rows visible when refreshing fails.
  setState((previous) => ({
    ...previous,
    loading: false,
    error: result.reason.message,
  }))
}

export function useWorkspaceData(organization) {
  const [transactions, setTransactions] = useState(initial)
  const [lineItems, setLineItems] = useState(initial)
  const [page, setPage] = useState(1)
  const activeRequest = useRef(null)

  const load = useCallback(
    (requestedPage) => {
      activeRequest.current?.abort()

      const controller = new AbortController()
      activeRequest.current = controller

      // One failed list should not discard the other list's response.
      return Promise.allSettled([
        getTransactions(organization, requestedPage, controller.signal),
        getLineItems(organization, controller.signal),
      ]).then(([transactionResult, lineItemResult]) => {
        // An older organization or page request must not replace the current rows.
        if (controller.signal.aborted) {
          return false
        }

        if (transactionResult.status === 'fulfilled') {
          setPage(requestedPage)
        }

        updateListState(transactionResult, setTransactions)
        updateListState(lineItemResult, setLineItems)

        return (
          transactionResult.status === 'fulfilled' &&
          lineItemResult.status === 'fulfilled'
        )
      })
    },
    [organization],
  )

  useEffect(() => {
    load(1)

    return () => activeRequest.current?.abort()
  }, [load])

  function changePage(requestedPage) {
    setTransactions((previous) => ({ ...previous, loading: true, error: '' }))
    setLineItems((previous) => ({ ...previous, loading: true, error: '' }))

    return load(requestedPage)
  }

  return {
    transactions,
    lineItems,
    page,
    loading: transactions.loading || lineItems.loading,
    refresh: () => changePage(page),
    changePage,
  }
}
