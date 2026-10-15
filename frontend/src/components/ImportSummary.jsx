import { Button } from '@mantine/core'
import { getImportFeedback } from '../utils/importFeedback'
import styles from './ImportSummary.module.css'

export function ImportSummary({ summary, onOpen, detailsButtonRef, embedded = false }) {
  if (!summary) {
    return null
  }

  return (
    <section
      className={styles.summary}
      data-embedded={embedded || undefined}
      aria-label={embedded ? 'Import details' : 'Import results'}
    >
      <div role="status">
        {!embedded && <strong>{getImportFeedback(summary).title}</strong>}
        <span className={styles.filename}>{summary.filename}</span>
        <p>
          {summary.imported} imported · {summary.duplicates} duplicates skipped ·{' '}
          {summary.errors.length} invalid rows
        </p>
      </div>

      {onOpen && (
        <Button
          variant="subtle"
          size="compact-sm"
          onClick={onOpen}
          ref={detailsButtonRef}
          className={styles.detailsButton}
        >
          View import details
        </Button>
      )}

      {/* Show invalid rows immediately so skipped payments are easy to identify. */}
      {summary.errors.length > 0 && (
        <details open className={styles.details}>
          <summary>Invalid rows ({summary.errors.length})</summary>
          <ul>
            {summary.errors.map((error, index) => (
              <li key={`${error.line}-${index}`}>
                <strong>Line {error.line}</strong>: {error.message}
              </li>
            ))}
          </ul>
        </details>
      )}

      {summary.duplicate_rows.length > 0 && (
        <details className={styles.details}>
          <summary>Skipped duplicates ({summary.duplicates})</summary>
          <ul>
            {summary.duplicate_rows.map((row) => (
              <li key={row.line}>
                Line {row.line}: {row.reference}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  )
}
