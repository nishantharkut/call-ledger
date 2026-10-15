import { MantineProvider } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useState } from 'react'
import { ReconciliationPage } from './pages/ReconciliationPage'
import { theme } from './theme'
import { WorkspaceNotifications } from './components/WorkspaceNotifications'

function App() {
  const [organization, setOrganization] = useState('northwind')

  function changeOrganization(value) {
    // Feedback from the previous organization should not follow the switch.
    notifications.clean()
    setOrganization(value)
  }

  return (
    <MantineProvider theme={theme} forceColorScheme="light">
      <WorkspaceNotifications />

      {/* Reset pending UI and imported-file details when the organization changes. */}
      <ReconciliationPage
        key={organization}
        organization={organization}
        onOrganizationChange={changeOrganization}
      />
    </MantineProvider>
  )
}

export default App
