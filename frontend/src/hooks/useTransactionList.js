import { useCallback, useEffect, useRef, useState } from 'react'
import { useDebouncedValue } from '@mantine/hooks'
import { getTransactions } from '../api/reconciliation'

export function useTransactionList(organization) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [ordering, setOrdering] = useState('-date')
  const [debouncedSearch] = useDebouncedValue(search.trim(), 350)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [state, setState] = useState({
    data: null,
    loading: true,
    error: '',
    query: '',
    pageSize: 50,
  })
  const activeRequest = useRef(null)
  const query = JSON.stringify([debouncedSearch, status, ordering, pageSize])

  const fetchPage = useCallback(
    (requestedPage) => {
      activeRequest.current?.abort()
      const controller = new AbortController()
      activeRequest.current = controller

      const filters = { search: debouncedSearch, status, ordering, pageSize }

      return getTransactions(organization, requestedPage, filters, controller.signal)
        .catch((error) => {
          // A review can remove the final row from the current filtered page.
          if (error.status !== 404 || requestedPage === 1 || controller.signal.aborted) {
            throw error
          }

          requestedPage = 1
          return getTransactions(organization, requestedPage, filters, controller.signal)
        })
        .then((data) => {
          if (controller.signal.aborted) {
            return false
          }

          setPage(requestedPage)
          setState({ data, loading: false, error: '', query, pageSize })
          return true
        })
        .catch((error) => {
          if (!controller.signal.aborted) {
            // Keep the last rows visible but prevent reviews until a retry succeeds.
            setState((previous) => ({
              ...previous,
              loading: false,
              error: error.message,
              query,
            }))
          }

          return false
        })
    },
    [organization, debouncedSearch, status, ordering, pageSize, query],
  )

  useEffect(() => {
    fetchPage(1)

    return () => activeRequest.current?.abort()
  }, [fetchPage])

  // Disable reviews during the debounce interval as well as the network request.
  const waiting = search.trim() !== debouncedSearch || state.query !== query

  function loadPage(requestedPage) {
    setState((previous) => ({ ...previous, loading: true, error: '' }))
    return fetchPage(requestedPage)
  }

  function clearFilters() {
    setSearch('')
    setStatus('')
  }

  return {
    state: {
      ...state,
      loading: state.loading || waiting,
      error: waiting ? '' : state.error,
    },
    page,
    pageSize,
    setPageSize,
    loading: state.loading || waiting,
    filters: { search, status, ordering },
    filtered: Boolean(search.trim() || status),
    setSearch,
    setStatus,
    setOrdering,
    clearFilters,
    loadPage,
  }
}
