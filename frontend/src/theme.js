import { createTheme } from '@mantine/core'

export const theme = createTheme({
  fontFamily: 'Commissioner, sans-serif',
  primaryColor: 'ledger',
  primaryShade: 7,
  defaultRadius: 'sm',
  headings: { fontFamily: 'Commissioner, sans-serif', fontWeight: '600' },
  // Mantine expects ten shades ordered from lightest to darkest.
  colors: {
    ledger: [
      '#f2f5f8',
      '#e5ecf2',
      '#c9d9e5',
      '#abc2d4',
      '#81a2bb',
      '#6389a5',
      '#4b728f',
      '#3c617e',
      '#30526d',
      '#24425b',
    ],
  },
  components: {
    Button: { defaultProps: { fw: 500 } },
    Badge: { defaultProps: { radius: 'sm', variant: 'light', fw: 500 } },
  },
})
