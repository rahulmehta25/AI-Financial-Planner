/**
 * Auth Service Wrapper
 * Provides backward compatibility for components using authService
 */

export { authService as default, authService } from './auth'
export type { User } from './auth'