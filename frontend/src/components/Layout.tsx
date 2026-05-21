/**
 * Layout principal - sidebar fixa estilo corporativo + header.
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Calendar, Kanban, BarChart2, Settings,
  Bell, LogOut, Users, Search,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/endpoints'
import ThemeToggle from './ThemeToggle'

type Perfil = 'colaborador' | 'lider' | 'rh' | 'diretoria' | 'admin'

const NAV_ITEMS: Array<{
  to: string
  icon: typeof Calendar
  label: string
  perfis: Perfil[]
}> = [
  { to: '/dashboard',  icon: LayoutDashboard, label: 'Dashboard',       perfis: ['colaborador','lider','rh','diretoria','admin'] },
  { to: '/agenda',     icon: Calendar,        label: 'Minha Agenda',    perfis: ['colaborador','lider','rh','diretoria','admin'] },
  { to: '/kanban',     icon: Kanban,          label: 'Kanban',          perfis: ['colaborador','lider','rh','diretoria','admin'] },
  { to: '/lider',      icon: Users,           label: 'Dashboard Lider', perfis: ['lider','admin'] },
  { to: '/relatorios', icon: BarChart2,       label: 'Relatorios',      perfis: ['rh','diretoria','admin'] },
  { to: '/admin',      icon: Settings,        label: 'Admin',           perfis: ['admin'] },
]

function initials(nome?: string): string {
  if (!nome) return '?'
  const parts = nome.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
  return (first + last).toUpperCase() || '?'
}

export default function Layout() {
  const { usuario, tenant, logout, refreshToken } = useAuthStore() as any
  const navigate = useNavigate()

  const handleLogout = async () => {
    try { if (refreshToken) await authApi.logout(refreshToken) } catch { /* ignore */ }
    logout()
    navigate('/login')
  }

  const filteredNav = NAV_ITEMS.filter(
    (item) => usuario?.perfil && item.perfis.includes(usuario.perfil as Perfil)
  )

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--color-bg)' }}>
      <aside style={{
        width: 248, flexShrink: 0,
        background: 'var(--color-surface)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '18px 20px',
          borderBottom: '1px solid var(--color-border)',
          minHeight: 64,
        }}>
          <div className="gradient-primary" style={{
            width: 38, height: 38, borderRadius: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 700, fontSize: 14,
            boxShadow: 'var(--shadow-sm)',
          }}>AH</div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text)', lineHeight: 1.2 }}>
              Agenda Hora a Hora
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
              {tenant?.nome ?? 'Workspace'}
            </div>
          </div>
        </div>

        <nav style={{ flex: 1, padding: 14, display: 'flex', flexDirection: 'column', gap: 4, overflowY: 'auto' }}>
          <div style={{
            fontSize: 11, fontWeight: 600,
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase', letterSpacing: '.08em',
            padding: '4px 8px 8px',
          }}>Menu</div>
          {filteredNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              id={`nav-${item.to.replace('/', '')}`}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <item.icon size={18} style={{ flexShrink: 0 }} />
              <span style={{ whiteSpace: 'nowrap' }}>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div style={{ padding: 14, borderTop: '1px solid var(--color-border)' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '10px 12px',
            background: 'var(--color-surface-muted)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'var(--color-primary)',
              color: '#fff', fontSize: 13, fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>{initials(usuario?.nome)}</div>
            <div style={{ overflow: 'hidden', flex: 1 }}>
              <div style={{
                fontSize: 13, fontWeight: 600, color: 'var(--color-text)',
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}>{usuario?.nome ?? 'Usuario'}</div>
              <div style={{
                fontSize: 11, color: 'var(--color-text-muted)',
                textTransform: 'capitalize',
              }}>{usuario?.perfil ?? '-'}</div>
            </div>
            <button
              id="btn-logout"
              onClick={handleLogout}
              title="Sair"
              style={{
                background: 'transparent', border: 'none',
                color: 'var(--color-text-muted)',
                cursor: 'pointer', display: 'flex',
                padding: 6, borderRadius: 6,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-danger)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <header style={{
          height: 64, flexShrink: 0,
          background: 'var(--color-surface)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'center',
          padding: '0 24px', gap: 16,
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '8px 14px',
            background: 'var(--color-surface-muted)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
            width: 360, maxWidth: '40vw',
          }}>
            <Search size={16} style={{ color: 'var(--color-text-muted)' }} />
            <input
              placeholder="Buscar tarefas, setores, pessoas..."
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                color: 'var(--color-text)', fontSize: 14,
              }}
            />
          </div>

          <div style={{ flex: 1 }} />

          <button id="btn-notifications" style={{
            position: 'relative', width: 38, height: 38,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
          }}>
            <Bell size={18} />
            <span style={{
              position: 'absolute', top: -4, right: -4,
              minWidth: 16, height: 16, padding: '0 4px',
              background: 'var(--color-danger)',
              color: '#fff', fontSize: 10, fontWeight: 700,
              borderRadius: 999,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '2px solid var(--color-surface)',
            }}>3</span>
          </button>

          <ThemeToggle />
        </header>

        <main style={{ flex: 1, overflow: 'auto', padding: 24, background: 'var(--color-bg)' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
