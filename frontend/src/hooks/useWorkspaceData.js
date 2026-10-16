import { useCallback, useEffect, useRef, useState } from 'react'
import { getLineItems } from '../api/reconciliation'
import { useTransactionList } from './useTransactionList'

export function useWorkspaceData(organization) {
  const transactionList = useTransactionList(organization)
  const [lineItems, setLineItems] = useState({ data: null, loading: true, error: '' })
  const activeRequest = useRef(null)

  const loadLineItems = useCallback(() => {
    activeRequest.current?.abort()
    const controller = new AbortController()
    activeRequest.current = controller

    return getLineItems(organization, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) {
          return false
        }

        setLineItems({ data, loading: false, error: '' })
        return true
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          setLineItems((previous) => ({
            ...previous,
            loading: false,
            error: error.message,
          }))
        }

        return false
      })
  }, [organization])

  useEffect(() => {
    loadLineItems()

    return () => activeRequest.current?.abort()
  }, [loadLineItems])

  async function refreshPage(requestedPage) {
    setLineItems((previous) => ({ ...previous, loading: true, error: '' }))

    // Imports and reviews refresh both lists. Browsing only reloads transactions.
    const results = await Promise.all([
      transactionList.loadPage(requestedPage),
      loadLineItems(),
    ])

    return results.every(Boolean)
  }

  return {
    transactions: transactionList.state,
    transactionList,
    lineItems,
    page: transactionList.page,
    loading: transactionList.loading || lineItems.loading,
    refresh: () => refreshPage(transactionList.page),
    refreshPage,
    changePage: transactionList.loadPage,
  }
}
