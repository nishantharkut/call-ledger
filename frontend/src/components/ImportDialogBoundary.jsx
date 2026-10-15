import { Component } from 'react'
import { Alert } from '@mantine/core'

export class ImportDialogBoundary extends Component {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    if (this.state.failed) {
      // A failed dialog download must not hide the imported rows or their summary.
      return (
        <Alert color="yellow" role="alert">
          Import results are available above. Reload the page to open the dialog.
        </Alert>
      )
    }

    return this.props.children
  }
}
