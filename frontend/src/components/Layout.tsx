/**
 * Layout principal — Sidebar + topbar + Outlet.
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  Calendar, LayoutKanban, BarChart2, Settings,
  Bell, LogOut, Menu, X, Users, ChevronRight
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/endpoints'

const NAV_ITEMS = [
  { to: '/agenda', icon: Calendar, label: 'Minha Agenda', perfis: ['colaborador', 'lider', 'rh', 'diretoria', 'admin'] },
  { to: '/kanban', icon: LayoutKanban, label: 'Kanban', perfis: ['colaborador', 'lider', 'rh', 'diretoria', 'admin'] },
  { to: '/lider', icon: Users, label: 'Dashboard Líder', perfis: ['lider', 'admin'] },
  { to: '/relatorios', icon: BarChart2, label: 'Relatórios', perfis: ['rh', 'diretoria', 'admin'] },
  { to: '/admin', icon: Settings, label: 'Admin', perfis: ['admin'] },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { usuario, tenant, logout, refreshToken } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      if (refreshToken) await authApi.logout(refreshToken)
    } catch { /* ignora */ }
    logout()
    navigate('/login')
  }

  const filteredNav = NAV_ITEMS.filter(item =>
    usuario?.perfil && item.perfis.includes(usuario.perfil)
  )

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <aside style={{
        width: sidebarOpen ? '240px' : '64px',
        transition: 'width 0.3s ease',
        background: 'var(--color-surface-elevated)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{
          padding: '1.25rem',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          minHeight: '64px',
        }}>
          <div style={{
            width: '36px', height: '36px', flexShrink: 0,
            borderRadius: '10px',
            background: `linear-gradient(135deg, var(--color-primary), var(--color-primary-light))`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.1rem',
          }}>📅</div>
          {sidebarOpen && (
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--color-text)', whiteSpace: 'nowrap' }}>
                Agenda H/H
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                {tenant?.nome}
              </div>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '0.75rem 0.5rem', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {filteredNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              id={`nav-${item.to.replace('/', '')}`}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.625rem 0.75rem',
                borderRadius: '10px',
                textDecoration: 'none',
                transition: 'all 0.15s ease',
                background: isActive ? `linear-gradient(135deg, var(--color-primary)33, var(--color-primary)22)` : 'transparent',
                border: isActive ? `1px solid var(--color-primary)44` : '1px solid transparent',
                color: isActive ? 'var(--color-text)' : 'var(--color-text-muted)',
              })}
            >
              <item.icon size={18} style={{ flexShrink: 0 }} />
              {sidebarOpen && (
                <span style={{ fontSize: '0.875rem', fontWeight: 500, whiteSpace: 'nowrap' }}>
                  {item.label}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div style={{
          padding: '0.75rem',
          borderTop: '1px solid var(--color-border)',
        }}>
          {sidebarOpen && (
            <div style={{
              padding: '0.75rem',
              borderRadius: '10px',
              background: 'rgba(255,255,255,0.04)',
              marginBottom: '0.5rem',
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text)' }}>
                {usuario?.nome}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>
                {usuario?.perfil}
              </div>
            </div>
          )}
          <button
            id="btn-logout"
            onClick={handleLogout}
            style={{
              width: '100%',
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.5rem 0.75rem',
              background: 'none', border: 'none',
              color: 'var(--color-text-muted)',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#ef4444')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
          >
            <LogOut size={16} />
            {sidebarOpen && 'Sair'}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Topbar */}
        <header style={{
          height: '64px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 1.5rem',
          gap: '1rem',
          background: 'var(--color-surface)',
          flexShrink: 0,
        }}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', display: 'flex' }}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div style={{ flex: 1 }} />
          <button
            id="btn-notifications"
            style={{
              background: 'none', border: '1px solid var(--color-border)',
              borderRadius: '8px', padding: '0.5rem',
              color: 'var(--color-text-muted)', cursor: 'pointer', display: 'flex',
              position: 'relative',
            }}
          >
            <Bell size={18} />
            <span style={{
              position: 'absolute', top: '-4px', right: '-4px',
              width: '16px', height: '16px',
              background: '#ef4444', borderRadius: '50%',
              fontSize: '0.6rem', color: 'white',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 700,
            }}>3</span>
          </button>
        </header>

        {/* Content */}
        <main style={{ flex: 1, overflow: 'auto', padding: '1.5rem' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
