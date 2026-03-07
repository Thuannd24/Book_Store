import { Button } from '../common/Button'
import { ErrorBanner } from '../common/ErrorBanner'

/**
 * Shared login card shell used by LoginPage, StaffLoginPage, ManagerLoginPage.
 * Props:
 *   icon            – emoji string shown at top
 *   title           – heading text
 *   subtitle        – sub-heading text
 *   loading         – boolean, disables submit button
 *   apiError        – string error from backend
 *   onSubmit        – form submit handler (receives SyntheticEvent)
 *   formFields      – ReactNode rendered inside the <form> (Input elements)
 *   footer          – optional ReactNode rendered below the card form (links, etc.)
 *   containerClassName – outer wrapper class (defaults to full-screen centred)
 */
export function BaseLoginForm({
  icon,
  title,
  subtitle,
  loading,
  apiError,
  onSubmit,
  formFields,
  footer,
  containerClassName = 'min-h-screen bg-gray-100 flex items-center justify-center',
}) {
  return (
    <div className={containerClassName}>
      <div className="w-full max-w-md bg-white rounded-2xl shadow-md p-8">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">{icon}</div>
          <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
          <p className="text-gray-500 text-sm">{subtitle}</p>
        </div>

        <ErrorBanner message={apiError} />

        <form onSubmit={onSubmit} className="flex flex-col gap-4 mt-4">
          {formFields}
          <Button type="submit" loading={loading} size="lg" className="mt-2 w-full">
            Login
          </Button>
        </form>

        {footer}
      </div>
    </div>
  )
}
