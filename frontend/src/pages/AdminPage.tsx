/**
 * AdminPage — Configurações do tenant (Apenas Admin).
 * CRUD de Usuários, Business Units, Feriados e SetorConfig.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Settings, Users, Building, CalendarOff, Settings2 } from 'lucide-react'
import { adminApi } from '../api/endpoints'
import { useAuthStore } from '../store/authStore'

export default function AdminPage() {
  const { usuario } = useAuthStore()
  const [aba, setAba] = useState<'usuarios' | 'bus' | 'feriados' | 'config'>('usuarios')

  if (usuario?.perfil !== 'admin') {
    return <div className="p-8 text-center text-red-400">Acesso negado. Apenas administradores.</div>
  }

  return (
    <div className="flex flex-col h-full gap-6 max-w-5xl mx-auto">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings size={24} className="text-slate-400" />
            Administração
          </h1>
          <p className="text-sm text-slate-400 mt-1">Configurações globais do Tenant.</p>
        </div>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700/50 pb-px">
        <TabAba icon={Users} label="Usuários" ativo={aba === 'usuarios'} onClick={() => setAba('usuarios')} />
        <TabAba icon={Building} label="Business Units" ativo={aba === 'bus'} onClick={() => setAba('bus')} />
        <TabAba icon={CalendarOff} label="Feriados" ativo={aba === 'feriados'} onClick={() => setAba('feriados')} />
        <TabAba icon={Settings2} label="Config Setor" ativo={aba === 'config'} onClick={() => setAba('config')} />
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto bg-slate-800/20 border border-slate-700/50 rounded-xl p-4">
        {aba === 'usuarios' && <TabUsuarios />}
        {aba === 'bus' && <div className="text-slate-400 p-4">Gestão de BUs em construção...</div>}
        {aba === 'feriados' && <div className="text-slate-400 p-4">Gestão de Feriados em construção...</div>}
        {aba === 'config' && <div className="text-slate-400 p-4">Configuração dinâmica de setores em construção...</div>}
      </div>
    </div>
  )
}

function TabAba({ icon: Icon, label, ativo, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 border-b-2 font-medium text-sm transition-colors ${
        ativo 
          ? 'border-blue-500 text-blue-400 bg-blue-500/10 rounded-t-lg' 
          : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-t-lg'
      }`}
    >
      <Icon size={16} /> {label}
    </button>
  )
}

function TabUsuarios() {
  const { data: usuarios = [], isLoading } = useQuery({
    queryKey: ['admin_usuarios'],
    queryFn: () => adminApi.usuarios.listar().then(res => res.data),
  })

  if (isLoading) return <div className="text-slate-400">Carregando usuários...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Lista de Usuários</h2>
        <button className="btn-primary py-1.5 px-3 text-sm">Novo Usuário</button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-800/80 text-slate-300">
            <tr>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">E-mail</th>
              <th className="px-4 py-3 font-medium">Perfil</th>
              <th className="px-4 py-3 font-medium">BU</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {usuarios.map((u: any) => (
              <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                <td className="px-4 py-3 font-medium">{u.nome}</td>
                <td className="px-4 py-3 text-slate-400">{u.email}</td>
                <td className="px-4 py-3 capitalize">{u.perfil}</td>
                <td className="px-4 py-3 text-slate-400">{u.bu_nome || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    u.ativo ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
                  }`}>
                    {u.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                </td>
              </tr>
            ))}
            {usuarios.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">Nenhum usuário encontrado.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
