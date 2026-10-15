import { Notification } from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { Check, CircleAlert, CircleX, Info } from 'lucide-react'
import styles from './WorkspaceNotifications.module.css'

const appearances = {
  green: { icon: Check, color: '#247448' },
  yellow: { icon: CircleAlert, color: '#76500b' },
  red: { icon: CircleX, color: '#b23b3b' },
  ledger: { icon: Info, color: '#30526d' },
}

export function WorkspaceNotifications() {
  return (
    <Notifications
      position="bottom-right"
      containerWidth={360}
      limit={1}
      autoClose={4000}
      transitionDuration={150}
      renderNotification={(notification) => {
        const appearance = appearances[notification.color] || appearances.ledger
        const StatusIcon = appearance.icon

        return (
          <Notification
            color={appearance.color}
            icon={<StatusIcon size={18} aria-hidden="true" />}
            onClose={() => notifications.hide(notification.id)}
            closeButtonProps={{ 'aria-label': 'Dismiss notification' }}
            role={notification.role || 'status'}
            classNames={{
              root: styles.toast,
              icon: styles.icon,
              description: styles.message,
              closeButton: styles.close,
            }}
          >
            {notification.message}
          </Notification>
        )
      }}
    />
  )
}
