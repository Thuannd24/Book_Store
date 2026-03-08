import { Modal } from './Modal'
import { Button } from './Button'

/**
 * Reusable confirmation dialog.
 * Props:
 *   isOpen    – boolean
 *   onClose   – called on cancel or backdrop click
 *   onConfirm – called on confirm button
 *   title     – dialog title (default: "Are you sure?")
 *   message   – body text
 *   confirmLabel – confirm button text (default: "Confirm")
 *   danger    – if true, confirm button is red
 */
export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = 'Are you sure?',
  message = 'This action cannot be undone.',
  confirmLabel = 'Confirm',
  danger = false,
}) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button variant={danger ? 'danger' : 'primary'} onClick={() => { onConfirm(); onClose() }}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-gray-600 text-sm">{message}</p>
    </Modal>
  )
}
