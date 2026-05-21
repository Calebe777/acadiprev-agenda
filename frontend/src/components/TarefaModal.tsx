import { useState } from 'react'
import { X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { tarefaApi } from '../api/endpoints'
import { useAuthStore } from '../store/authStore'

interface TarefaModalProps {
  onClose: () => void
}

export default function TarefaModal({ onClose }: TarefaModalProps) {
  const queryClient = useQueryClient()
  const { usuario } = useAuthStore() as any
  const [titulo, setTitulo] = useState('')
  const [prioridade, setPrioridade] = useState('media')
  const [prazo, setPrazo] = useState('')

  const criarMutation = useMutation({
    mutationFn: (payload: any) => tarefaApi.criar(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tarefas'] })
      onClose()
    },
    onError: (err) => alert('Erro ao criar tarefa: ' + String(err))
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    criarMutation.mutate({
      titulo,
      prioridade,
      prazo: prazo || null,
      status: 'a_fazer',
      bu_id: usuario?.bu_id || undefined,
      ordem_kanban: 0
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-slate-700/50 bg-slate-800/50">
          <h2 className="text-lg font-bold text-slate-100">Nova Tarefa</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Título</label>
            <input
              required
              autoFocus
              className="input bg-slate-800 border-slate-700"
              value={titulo}
              onChange={e => setTitulo(e.target.value)}
              placeholder="O que precisa ser feito?"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Prioridade</label>
              <select
                className="input bg-slate-800 border-slate-700"
                value={prioridade}
                onChange={e => setPrioridade(e.target.value)}
              >
                <option value="baixa">Baixa</option>
                <option value="media">Média</option>
                <option value="alta">Alta</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Prazo</label>
              <input
                type="date"
                className="input bg-slate-800 border-slate-700"
                value={prazo}
                onChange={e => setPrazo(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-700/50">
            <button type="button" onClick={onClose} className="btn-ghost">
              Cancelar
            </button>
            <button type="submit" disabled={criarMutation.isPending} className="btn-primary">
              {criarMutation.isPending ? 'Criando...' : 'Criar Tarefa'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
