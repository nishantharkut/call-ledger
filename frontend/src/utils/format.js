const integerFormat = new Intl.NumberFormat('en-US')
export const DISPLAY_CURRENCY = 'USD'
const dateFormat = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})

export function formatMoney(value) {
  const [integer, fraction = '00'] = String(value).split('.')

  // Keep the integer exact even when it exceeds JavaScript's safe number range.
  const negative = integer.startsWith('-')
  const digits = negative ? integer.slice(1) : integer

  return `${negative ? '-' : ''}$${integerFormat.format(BigInt(digits))}.${fraction.padEnd(2, '0')}`
}

export function formatDate(value) {
  // Bank dates have no timezone. Display the stored calendar date unchanged.
  return dateFormat.format(new Date(`${value}T00:00:00Z`))
}
