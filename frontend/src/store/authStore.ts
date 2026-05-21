/**
 * Store de autenticação — Zustand
 * Gerencia tokens JWT, dados do usuário e config do tenant.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Usuario {
  id?: string
  nome: string
  email?: string
  perfil: 'colaborador' | 'lider' | 'rh' | 'diretoria' | 'admin' | string
  bu_id: string | null
  schema_name?: string
  tenant_nome?: string
}

interface TenantConfig {
  nome: string
  cor_primaria: string
  logo_url: string
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  usuario: Usuario | null
  tenant: TenantConfig | null

  setTokens: (access: string, refresh: string) => void
  setUsuario: (user: Usuario) => void
  setTenant: (tenant: TenantConfig) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      usuario: null,
      tenant: null,

      setTokens: (access, refresh) => {
        localStorage.setItem('access_token', access)
        localStorage.setItem('refresh_token', refresh)
        set({ accessToken: access, refreshToken: refresh })
      },

      setUsuario: (usuario) => set({ usuario }),

      setTenant: (tenant) => {
        // Aplica tema dinamicamente via CSS Custom Properties
        if (tenant.cor_primaria) {
          const root = document.documentElement
          root.style.setProperty('--color-primary', tenant.cor_primaria)
          // Versão mais clara (clareia 20%)
          root.style.setProperty('--color-primary-light', lightenColor(tenant.cor_primaria, 20))
          root.style.setProperty('--color-primary-dark', lightenColor(tenant.cor_primaria, -15))
        }
        set({ tenant })
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ accessToken: null, refreshToken: null, usuario: null })
        window.location.href = '/login'
      },

      isAuthenticated: () => !!get().accessToken && !!get().usuario,
    }),
    { name: 'auth-store', partialize: (state) => ({ accessToken: state.accessToken, refreshToken: state.refreshToken, usuario: state.usuario }) }
  )
)

/** Clareia ou escurece uma cor hex. */
function lightenColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.max(0, Math.min(255, (num >> 16) + amount))
  const g = Math.max(0, Math.min(255, ((num >> 8) & 0xff) + amount))
  const b = Math.max(0, Math.min(255, (num & 0xff) + amount))
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}
