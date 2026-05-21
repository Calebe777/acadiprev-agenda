import { useState } from 'react'
import { X, Upload } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { blocoApi } from '../api/endpoints'

interface ConcluirBlocoModalProps {
  blocoId: string
  onClose: () => void
}

export default function ConcluirBlocoModal({ blocoId, onClose }: ConcluirBlocoModalProps) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState('concluido')
  const [descricao, setDescricao] = useState('')
  const [arquivo, setArquivo] = useState<File | null>(null)

  const concluirMutation = useMutation({
    mutationFn: (formData: FormData) => blocoApi.concluir(blocoId, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agenda'] })
      onClose()
    },
    onError: (err) => alert('Erro ao concluir bloco: ' + String(err))
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData()
    formData.append('status', status)
    formData.append('descricao', descricao)
    if (arquivo) {
      formData.append('evidencia_arquivo', arquivo)
    }
    concluirMutation.mutate(formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-slate-700/50 bg-slate-800/50">
          <h2 className="text-lg font-bold text-slate-100">Concluir Bloco</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Status Final</label>
            <select
              className="input bg-slate-800 border-slate-700"
              value={status}
              onChange={e => setStatus(e.target.value)}
            >
              <option value="concluido">Concluído</option>
              <option value="parcial">Parcial (incompleto)</option>
              <option value="desviado">Desviado (fiz outra coisa)</option>
              <option value="nao_realizado">Não Realizado</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Descrição / Resumo
            </label>
            <textarea
              required
              rows={3}
              className="input bg-slate-800 border-slate-700 resize-none"
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              placeholder="Descreva o que foi feito..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Evidência (Opcional)
            </label>
            <label className="flex items-center justify-center gap-2 border-2 border-dashed border-slate-600 rounded-lg p-4 cursor-pointer hover:bg-slate-800 hover:border-slate-500 transition-colors">
              <Upload size={16} className="text-slate-400" />
              <span className="text-sm text-slate-300">
                {arquivo ? arquivo.name : 'Selecionar arquivo...'}
              </span>
              <input
                type="file"
                className="hidden"
                onChange={e => setArquivo(e.target.files?.[0] || null)}
              />
            </label>
          </div>

          <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-700/50">
            <button type="button" onClick={onClose} className="btn-ghost">
              Cancelar
            </button>
            <button type="submit" disabled={concluirMutation.isPending} className="btn-primary bg-green-600 hover:bg-green-500">
              {concluirMutation.isPending ? 'Salvando...' : 'Finalizar Bloco'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
