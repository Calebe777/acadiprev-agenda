import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/endpoints'
import { Lock, Mail } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const { setTokens, setUsuario } = useAuthStore()
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      const res = await authApi.login(email, password)
      setTokens(res.data.access, res.data.refresh)
      setUsuario({
        id: res.data.usuario?.id,
        nome: res.data.usuario?.nome || email,
        email: res.data.usuario?.email || email,
        perfil: res.data.usuario?.perfil || 'colaborador',
        bu_id: res.data.usuario?.bu_id,
        schema_name: res.data.usuario?.schema_name,
        tenant_nome: res.data.usuario?.tenant_nome,
      })
      navigate('/agenda')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao realizar login. Verifique suas credenciais.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-[var(--color-surface)]">
      <div className="card w-full max-w-md shadow-2xl relative overflow-hidden">
        {/* Decorative background element */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-32 h-32 rounded-full bg-[var(--color-primary)] opacity-10 blur-2xl"></div>
        <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-32 h-32 rounded-full bg-[var(--color-accent)] opacity-10 blur-2xl"></div>

        <div className="text-center mb-8 relative z-10">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-light)] mx-auto mb-4 flex items-center justify-center text-3xl shadow-lg shadow-[var(--color-primary)]/20">
            📅
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Bem-vindo de volta</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-2">Acesse sua agenda H/H</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg mb-6 text-sm text-center relative z-10 slide-up">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="flex flex-col gap-5 relative z-10">
          <div>
            <label className="block text-sm font-medium mb-1.5 text-[var(--color-text)]">E-mail</label>
            <div className="relative group">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] group-focus-within:text-[var(--color-accent)] transition-colors" size={18} />
              <input
                type="email"
                required
                className="input pl-10"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1.5 text-[var(--color-text)]">Senha</label>
            <div className="relative group">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] group-focus-within:text-[var(--color-accent)] transition-colors" size={18} />
              <input
                type="password"
                required
                className="input pl-10"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full justify-center mt-2 py-2.5"
          >
            {isLoading ? 'Entrando...' : 'Entrar no sistema'}
          </button>
        </form>
      </div>
    </div>
  )
}
