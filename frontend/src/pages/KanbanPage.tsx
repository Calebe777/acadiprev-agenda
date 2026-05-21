/**
 * KanbanPage — Gerenciamento de tarefas (dnd-kit simplificado para UI estática sem a lib).
 * Mostra tarefas em A fazer, Em andamento e Concluído.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Clock, AlertCircle, CheckCircle2, User } from 'lucide-react'
import { tarefaApi } from '../api/endpoints'
import { useAuthStore } from '../store/authStore'
import TarefaModal from '../components/TarefaModal'

export default function KanbanPage() {
  const { usuario } = useAuthStore()
  const [filtro, setFiltro] = useState('minhas') // minhas, bu (se líder)
  const [showModal, setShowModal] = useState(false)

  const { data: tarefas = [], isLoading } = useQuery({
    queryKey: ['tarefas', filtro],
    queryFn: () => 
      filtro === 'bu' && usuario?.bu_id
        ? tarefaApi.porBU(usuario.bu_id).then(res => res.data.results || res.data)
        : tarefaApi.listar().then(res => res.data.results || res.data),
  })

  // Agrupa tarefas por status
  const colunas = {
    a_fazer: tarefas.filter((t: any) => t.status === 'a_fazer').sort((a: any, b: any) => a.ordem_kanban - b.ordem_kanban),
    em_andamento: tarefas.filter((t: any) => t.status === 'em_andamento').sort((a: any, b: any) => a.ordem_kanban - b.ordem_kanban),
    concluido: tarefas.filter((t: any) => t.status === 'concluido').sort((a: any, b: any) => a.ordem_kanban - b.ordem_kanban),
  }

  if (isLoading) return <div className="p-8 text-center text-slate-400">Carregando quadro...</div>

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Kanban de Tarefas</h1>
          <p className="text-sm text-slate-400 mt-1">Gerencie suas entregas e backlogs.</p>
        </div>
        
        <div className="flex items-center gap-4">
          {usuario?.perfil === 'lider' && (
            <select 
              className="input py-1.5 px-3 w-auto bg-slate-800"
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
            >
              <option value="minhas">Minhas Tarefas</option>
              <option value="bu">Tarefas da BU</option>
            </select>
          )}
          <button className="btn-primary py-2" onClick={() => setShowModal(true)}>
            <Plus size={16} /> Nova Tarefa
          </button>
        </div>
      </header>

      {/* Colunas do Kanban */}
      <div className="flex-1 flex gap-6 overflow-x-auto pb-4">
        <ColunaKanban titulo="A Fazer" tarefas={colunas.a_fazer} cor="slate" />
        <ColunaKanban titulo="Em Andamento" tarefas={colunas.em_andamento} cor="blue" />
        <ColunaKanban titulo="Concluído" tarefas={colunas.concluido} cor="green" />
      </div>

      {showModal && <TarefaModal onClose={() => setShowModal(false)} />}
    </div>
  )
}

function ColunaKanban({ titulo, tarefas, cor }: { titulo: string, tarefas: any[], cor: string }) {
  const cores = {
    slate: 'bg-slate-800/50 border-slate-700/50',
    blue: 'bg-blue-900/20 border-blue-800/30',
    green: 'bg-green-900/20 border-green-800/30',
  }

  return (
    <div className={`flex flex-col w-80 shrink-0 rounded-xl border ${cores[cor as keyof typeof cores]} overflow-hidden`}>
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/5">
        <h2 className="font-semibold">{titulo}</h2>
        <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full">
          {tarefas.length}
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
        {tarefas.map(tarefa => (
          <CardTarefa key={tarefa.id} tarefa={tarefa} />
        ))}
        {tarefas.length === 0 && (
          <div className="text-center p-4 text-sm text-slate-500 border border-dashed border-slate-700/50 rounded-lg">
            Nenhuma tarefa.
          </div>
        )}
      </div>
    </div>
  )
}

function CardTarefa({ tarefa }: { tarefa: any }) {
  const prioridadeCores = {
    alta: 'text-red-400 bg-red-400/10 border-red-400/20',
    media: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
    baixa: 'text-slate-400 bg-slate-400/10 border-slate-400/20',
  }
  
  const corPrio = prioridadeCores[tarefa.prioridade as keyof typeof prioridadeCores] || prioridadeCores.media

  return (
    <div className="bg-slate-800/80 border border-slate-700 p-3 rounded-lg shadow-sm hover:border-slate-500 transition-colors cursor-grab active:cursor-grabbing">
      <div className="flex justify-between items-start mb-2">
        <span className={`text-[10px] px-1.5 py-0.5 rounded border uppercase font-bold tracking-wider ${corPrio}`}>
          {tarefa.prioridade}
        </span>
        {tarefa.prazo_vencido && (
          <span className="text-[10px] flex items-center gap-1 text-red-400 font-bold">
            <AlertCircle size={10} /> Vencida
          </span>
        )}
      </div>
      
      <h3 className="text-sm font-medium leading-tight mb-2 text-slate-100">{tarefa.titulo}</h3>
      
      {tarefa.bloco_detalhe && (
        <div className="text-xs text-blue-400 mb-2 flex items-center gap-1 bg-blue-400/10 p-1 rounded inline-flex">
          <CheckCircle2 size={12} /> {tarefa.bloco_detalhe.atividade}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-slate-400 mt-3 pt-3 border-t border-slate-700/50">
        <div className="flex items-center gap-1">
          <Clock size={12} />
          {tarefa.prazo ? new Date(tarefa.prazo).toLocaleDateString('pt-BR') : 'Sem prazo'}
        </div>
        
        {tarefa.atribuido_a && (
          <div className="flex items-center gap-1 bg-slate-700/50 px-1.5 py-0.5 rounded">
            <User size={10} />
            <span className="truncate max-w-[80px]" title={tarefa.atribuido_a.nome}>
              {tarefa.atribuido_a.nome.split(' ')[0]}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
