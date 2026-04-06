/**
 * Shared hook for accessing the current company ID.
 * Used across pages that need company-scoped API calls.
 */
export function useCompanyId(): string {
  return localStorage.getItem("company_id") || ""
}
