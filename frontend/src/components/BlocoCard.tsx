/**
 * BlocoCard — Renderiza um bloco na tela da Agenda e gerencia o modal de Conclusão Dinâmica.
 * Usa as regras de validação baseadas no tipo de setor (SetorConfig).
 */
import { useState } from 'react'
import { PlayCircle, CheckCircle2, Lock, FileText, AlertCircle, X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { blocoApi } from '../api/endpoints'

interface BlocoCardProps {
  bloco: any
  podeEditar: boolean
}

export default function BlocoCard({ bloco, podeEditar }: BlocoCardProps) {
  const [modalAberto, setModalAberto] = useState(false)
  const queryClient = useQueryClient()

  const iniciarMutation = useMutation({
    mutationFn: (id: string) => blocoApi.iniciar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agenda'] })
  })

  return (
    <>
      <div className="card relative overflow-hidden transition-all hover:border-slate-600">
        {bloco.registro?.status === 'em_andamento' && (
          <div className="absolute top-0 left-0 w-1 h-full bg-green-500" />
        )}
        
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg font-bold text-slate-200">
                {bloco.horario_inicio.substring(0, 5)} {bloco.horario_fim && `- ${bloco.horario_fim.substring(0, 5)}`}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {bloco.tipo}
              </span>
              {bloco.registro?.confidencial && (
                <span className="text-xs flex items-center gap-1 text-orange-400">
                  <Lock size={12} /> Confidencial
                </span>
              )}
            </div>
            
            <h3 className="text-base font-medium text-slate-100">{bloco.atividade}</h3>
            {bloco.foco_entrega && (
              <p className="text-sm text-slate-400 mt-1 flex items-start gap-1">
                <FileText size={14} className="mt-0.5 flex-shrink-0" />
                {bloco.foco_entrega}
              </p>
            )}
          </div>

          <div className="flex flex-col items-end gap-2 ml-4">
            <BadgeRegistro status={bloco.registro?.status} />
            
            {podeEditar && (
              <div className="mt-2 flex gap-2">
                {bloco.registro?.status === 'pendente' && (
                  <button
                    onClick={() => iniciarMutation.mutate(bloco.id)}
                    disabled={iniciarMutation.isPending}
                    className="btn-secondary px-3 py-1 text-xs"
                  >
                    <PlayCircle size={14} /> Iniciar
                  </button>
                )}
                
                {bloco.registro?.status === 'em_andamento' && (
                  <button
                    onClick={() => setModalAberto(true)}
                    className="btn-primary px-3 py-1 text-xs"
                  >
                    <CheckCircle2 size={14} /> Concluir
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {modalAberto && (
        <ModalConclusao 
          bloco={bloco} 
          onClose={() => setModalAberto(false)} 
        />
      )}
    </>
  )
}

function ModalConclusao({ bloco, onClose }: { bloco: any, onClose: () => void }) {
  const [status, setStatus] = useState('concluido')
  const [observacao, setObservacao] = useState('')
  const [evidencia, setEvidencia] = useState<File | null>(null)
  
  const queryClient = useQueryClient()
  const concluirMutation = useMutation({
    mutationFn: (formData: FormData) => blocoApi.concluir(bloco.id, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agenda'] })
      onClose()
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Simulação da validação da SetorConfig no front
    if (status !== 'concluido' && !observacao) {
      alert('É obrigatório preencher uma observação/justificativa quando o bloco não é 100% concluído.')
      return
    }

    const fd = new FormData()
    fd.append('status', status)
    fd.append('observacao', observacao)
    if (evidencia) fd.append('evidencia', evidencia)

    concluirMutation.mutate(fd)
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="card w-full max-w-md p-6 slide-up relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">
          <X size={20} />
        </button>
        
        <h2 className="text-xl font-bold mb-4">Concluir Atividade</h2>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Status Final</label>
            <select 
              className="input" 
              value={status} 
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="concluido">Concluído Totalmente</option>
              <option value="parcial">Parcial (Continuar Depois)</option>
              <option value="nao_realizado">Não Realizado (Impedimento)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1 flex items-center gap-1">
              Observações {status !== 'concluido' && <span className="text-orange-400">*obrigatório</span>}
            </label>
            <textarea 
              className="input min-h-[100px]"
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
              placeholder="Descreva o que foi entregue ou o motivo do impedimento..."
              required={status !== 'concluido'}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">Evidência (Opcional)</label>
            <input 
              type="file" 
              className="input file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-500/10 file:text-blue-400 hover:file:bg-blue-500/20"
              onChange={(e) => setEvidencia(e.target.files?.[0] || null)}
              accept="image/*,.pdf,.zip"
            />
            <p className="text-xs text-slate-500 mt-1">Imagens, PDFs ou ZIPs (máx 5MB)</p>
          </div>

          {status === 'nao_realizado' && (
            <div className="bg-orange-500/10 border border-orange-500/30 text-orange-400 p-3 rounded-lg text-sm flex gap-2">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              Uma justificativa formal será aberta e encaminhada para a sua liderança imediata.
            </div>
          )}

          <div className="flex justify-end gap-3 mt-4">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={concluirMutation.isPending} className="btn-primary">
              {concluirMutation.isPending ? 'Salvando...' : 'Finalizar Bloco'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function BadgeRegistro({ status }: { status: string }) {
  const map: Record<string, { c: string, l: string }> = {
    pendente: { c: 'text-slate-500', l: 'Pendente' },
    em_andamento: { c: 'text-green-500 font-medium flex items-center gap-1', l: 'Em andamento' },
    concluido: { c: 'text-blue-400 flex items-center gap-1', l: 'Concluído' },
    parcial: { c: 'text-yellow-500 flex items-center gap-1', l: 'Parcial' },
    nao_realizado: { c: 'text-red-500', l: 'Não realizado' },
    desviado: { c: 'text-orange-500 flex items-center gap-1', l: 'Desviado' },
  }
  const t = map[status] || map.pendente
  return (
    <span className={`text-xs ${t.c}`}>
      {status === 'em_andamento' && <span className="pulse-dot mr-1" />}
      {t.l}
    </span>
  )
}
