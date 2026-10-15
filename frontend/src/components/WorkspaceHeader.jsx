import { NativeSelect } from '@mantine/core'
import styles from '../pages/ReconciliationPage.module.css'

export function WorkspaceHeader({ organization, onChange, disabled }) {
  return (
    <header className={styles.headerSurface}>
      <div className={styles.header}>
        <a className={styles.brand} href="/" aria-label="CallLedger home">
          CallLedger
        </a>
        <div className={styles.organizationGroup}>
          <label htmlFor="organization" className={styles.organizationLabel}>
            Organization
          </label>
          {/* These organization slugs must match the seed_demo command. */}
          <NativeSelect
            id="organization"
            value={organization}
            onChange={(event) => onChange(event.currentTarget.value)}
            disabled={disabled}
            data={[
              { value: 'northwind', label: 'Northwind Ventures' },
              { value: 'bluebird', label: 'Bluebird Capital' },
            ]}
            className={styles.organization}
          />
        </div>
      </div>
    </header>
  )
}
