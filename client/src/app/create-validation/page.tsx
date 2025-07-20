import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { CreateValidationForm } from '@/components/validation/CreateValidationForm'

export default function CreateValidationPage() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8 px-4">
        <CreateValidationForm />
      </div>
    </ProtectedRoute>
  )
}