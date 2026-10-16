import { Button, NativeSelect, TextInput } from '@mantine/core'
import { Search } from 'lucide-react'
import styles from './TransactionControls.module.css'

export function TransactionControls({ list, disabled, loading }) {
  return (
    <div className={styles.controls} role="group" aria-label="Transaction controls">
      <TextInput
        label="Search transactions"
        placeholder="Description or bank reference"
        value={list.filters.search}
        onChange={(event) => list.setSearch(event.currentTarget.value)}
        leftSection={<Search size={16} aria-hidden="true" />}
        loading={loading}
        loadingPosition="left"
        leftSectionPointerEvents="none"
        leftSectionProps={
          loading ? { role: 'status', 'aria-label': 'Updating transactions' } : undefined
        }
        disabled={disabled}
        className={styles.search}
        type="search"
      />

      <NativeSelect
        label="Status"
        value={list.filters.status}
        onChange={(event) => list.setStatus(event.currentTarget.value)}
        disabled={disabled}
        data={[
          { value: '', label: 'All statuses' },
          { value: 'suggested', label: 'Suggested' },
          { value: 'needs_review', label: 'Needs review' },
          { value: 'reconciled', label: 'Reconciled' },
          { value: 'ignored', label: 'Ignored' },
        ]}
      />

      <NativeSelect
        label="Sort by"
        value={list.filters.ordering}
        onChange={(event) => list.setOrdering(event.currentTarget.value)}
        disabled={disabled}
        data={[
          { value: '-date', label: 'Newest first' },
          { value: 'date', label: 'Oldest first' },
          { value: '-amount', label: 'Highest amount' },
          { value: 'amount', label: 'Lowest amount' },
        ]}
      />

      {list.filtered && (
        <Button variant="default" onClick={list.clearFilters} disabled={disabled}>
          Clear filters
        </Button>
      )}
    </div>
  )
}
