/**
 * ThemeToggle — botão minimalista que alterna entre claro e escuro.
 */
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      id="btn-theme-toggle"
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
      title={isDark ? 'Tema claro' : 'Tema escuro'}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 38,
        height: 38,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)',
        color: 'var(--color-text-secondary)',
        cursor: 'pointer',
        transition: 'background .15s ease, border-color .15s ease, color .15s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'var(--color-surface-muted)'
        e.currentTarget.style.color = 'var(--color-text)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'var(--color-surface)'
        e.currentTarget.style.color = 'var(--color-text-secondary)'
      }}
    >
      {isDark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  )
}
