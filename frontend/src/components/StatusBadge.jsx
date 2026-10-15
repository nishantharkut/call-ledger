import { Badge } from '@mantine/core'

// Reserve green for completed states and blue for proposals or partial funding.
const statuses = {
  suggested: ['Suggested', 'blue'],
  needs_review: ['Needs review', 'yellow'],
  reconciled: ['Reconciled', 'teal'],
  ignored: ['Ignored', 'gray'],
  open: ['Open', 'gray'],
  partially_funded: ['Partially funded', 'blue'],
  funded: ['Funded', 'teal'],
  proposed: ['Proposed', 'blue'],
  approved: ['Approved', 'teal'],
  rejected: ['Rejected', 'red'],
}

export function StatusBadge({ status }) {
  const [label, color] = statuses[status] || [status, 'gray']

  const textColor = {
    yellow: '#76500b',
    blue: '#285a86',
    teal: '#256b56',
    gray: '#58616a',
    red: '#b23b3b',
  }[color]

  const backgroundColor = {
    yellow: '#faf1d8',
    blue: '#e9f0f7',
    teal: '#e7f2ec',
    gray: '#f0f2f4',
    red: '#faecec',
  }[color]

  return (
    <Badge
      variant="light"
      color={color}
      c={textColor}
      tt="none"
      size="lg"
      fz="0.8125rem"
      fw={500}
      w="8.5rem"
      h="1.75rem"
      px={8}
      radius="sm"
      style={{ letterSpacing: 0, backgroundColor }}
    >
      {label}
    </Badge>
  )
}
