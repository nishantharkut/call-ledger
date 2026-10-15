import { MantineProvider } from '@mantine/core'
import { useState } from 'react'
import { ReconciliationPage } from './pages/ReconciliationPage'
import { theme } from './theme'

function App() {
  const [organization, setOrganization] = useState('northwind')

  return (
    <MantineProvider theme={theme} forceColorScheme="light">
      {/* Reset pending UI and imported-file details when the organization changes. */}
      <ReconciliationPage
        key={organization}
        organization={organization}
        onOrganizationChange={setOrganization}
      />
    </MantineProvider>
  )
}

export default App
