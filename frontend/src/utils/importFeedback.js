export const IMPORT_NOTIFICATION_ID = 'statement-import'

export function getImportFeedback(result) {
  const invalid = result.errors.length
  const skipped = result.duplicates + invalid
  const importedMessage = `${result.imported} ${result.imported === 1 ? 'transaction' : 'transactions'} imported.`
  const message =
    skipped > 0
      ? `${importedMessage} ${skipped} ${skipped === 1 ? 'row' : 'rows'} skipped.`
      : importedMessage

  if (result.imported === 0) {
    if (invalid > 0) {
      return {
        title: 'No rows imported',
        color: 'yellow',
        message: 'No transactions imported. Check the row errors.',
      }
    }

    return {
      title: result.duplicates > 0 ? 'No new transactions' : 'No transactions found',
      color: 'ledger',
      message:
        result.duplicates > 0
          ? 'All transactions were already imported.'
          : 'The statement has no transactions.',
    }
  }

  if (invalid > 0 || result.duplicates > 0) {
    return {
      title: 'Import completed with skipped rows',
      color: invalid > 0 ? 'yellow' : 'green',
      message,
    }
  }

  return { title: 'Statement imported', color: 'green', message }
}
