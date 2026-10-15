import { Skeleton, VisuallyHidden } from '@mantine/core'
import { useReducedMotion } from '@mantine/hooks'
import styles from './TableSkeleton.module.css'

export function TableSkeleton({ label, columns }) {
  const reducedMotion = useReducedMotion()

  return (
    <div className={styles.surface} role="status" aria-label={label}>
      <VisuallyHidden>{label}</VisuallyHidden>

      <div aria-hidden="true" className={styles.table} style={{ '--columns': columns }}>
        <div className={`${styles.row} ${styles.heading}`}>
          {Array.from({ length: columns }, (_, column) => (
            <Skeleton key={column} height={12} width="60%" animate={!reducedMotion} />
          ))}
        </div>

        {Array.from({ length: 4 }, (_, row) => (
          <div className={styles.row} key={row}>
            {Array.from({ length: columns }, (_, column) => (
              <Skeleton key={column} height={14} width="80%" animate={!reducedMotion} />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
