/**
 * AgendaPage — Visão do dia para o colaborador.
 * Mostra blocos de horário, permite check-in, check-out e execução de atividades.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  CheckCircle2, PlayCircle, 
  CalendarCheck, CalendarX, Plus, FileText, Lock
} from 'lucide-react'
import { agendaApi, blocoApi } from '../api/endpoints'

export default function AgendaPage() {
  const queryClient = useQueryClient()
  const [hoje] = useState(() => new Date().toISOString().split('T')[0])

  // Fetch agenda do dia
  const { data, isLoading } = useQuery({
    queryKey: ['agenda', hoje],
    queryFn: () => agendaApi.hoje().then(res => res.data),
    retry: false, // 404 se não houver agenda
  })

  // Mutations
  const checkinMutation = useMutation({
    mutationFn: (id: string) => agendaApi.checkin(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agenda', hoje] }),
  })

  const checkoutMutation = useMutation({
    mutationFn: (id: string) => agendaApi.checkout(id, 'Fim do expediente.'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agenda', hoje] }),
  })

  const iniciarBlocoMutation = useMutation({
    mutationFn: (id: string) => blocoApi.iniciar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agenda', hoje] }),
  })

  if (isLoading) {
    return <div className="p-8 text-center text-gray-400">Carregando agenda...</div>
  }

  // Se não tem agenda (404), mostra botão para criar rascunho
  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
        <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-2">
          <CalendarX size={32} />
        </div>
        <h2 className="text-xl font-bold">Nenhuma agenda para hoje</h2>
        <p className="text-sm text-slate-400 max-w-sm">
          Sua liderança não gerou uma agenda ou você está de folga.
        </p>
        <button 
          onClick={() => agendaApi.criar({ data: hoje }).then(() => queryClient.invalidateQueries({ queryKey: ['agenda', hoje] }))}
          className="btn-primary mt-4"
        >
          <Plus size={18} /> Criar Agenda (Rascunho)
        </button>
      </div>
    )
  }

  const agenda = data
  const isReadonly = ['encerrado', 'aprovado'].includes(agenda.status)

  return (
    <div className="flex flex-col h-full gap-6 max-w-4xl mx-auto">
      {/* Header */}
      <header className="card flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            Minha Agenda <span className="text-sm font-normal text-slate-400">({new Intl.DateTimeFormat('pt-BR', { dateStyle: 'full' }).format(new Date(hoje))})</span>
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <BadgeStatus status={agenda.status} />
            <span className="text-sm text-slate-400 flex items-center gap-1">
              <CheckCircle2 size={14} className="text-blue-500" />
              {agenda.percentual_conclusao}% concluído
            </span>
          </div>
        </div>

        <div className="flex gap-3">
          {!agenda.check_in_at && agenda.status === 'rascunho' && (
            <button
              onClick={() => checkinMutation.mutate(agenda.id)}
              disabled={checkinMutation.isPending}
              className="btn-primary"
            >
              <CalendarCheck size={18} />
              Fazer Check-in
            </button>
          )}

          {agenda.status === 'ativo' && (
            <button
              onClick={() => {
                if (window.confirm('Tem certeza que deseja encerrar o dia?')) {
                  checkoutMutation.mutate(agenda.id)
                }
              }}
              disabled={checkoutMutation.isPending}
              className="btn-secondary"
            >
              Fazer Check-out
            </button>
          )}
        </div>
      </header>

      {/* Blocos de Horário */}
      <div className="flex-1 overflow-auto pr-2 flex flex-col gap-3">
        {agenda.blocos?.map((bloco: any) => (
          <div key={bloco.id} className="card relative overflow-hidden transition-all hover:border-slate-600">
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

              {/* Ações do bloco */}
              <div className="flex flex-col items-end gap-2 ml-4">
                <BadgeRegistro status={bloco.registro?.status} />
                
                {!isReadonly && agenda.status === 'ativo' && (
                  <div className="mt-2 flex gap-2">
                    {bloco.registro?.status === 'pendente' && (
                      <button
                        onClick={() => iniciarBlocoMutation.mutate(bloco.id)}
                        disabled={iniciarBlocoMutation.isPending}
                        className="btn-secondary px-3 py-1 text-xs"
                      >
                        <PlayCircle size={14} /> Iniciar
                      </button>
                    )}
                    
                    {bloco.registro?.status === 'em_andamento' && (
                      <button
                        onClick={() => alert('Abrir modal de conclusão')}
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
        ))}
        
        {agenda.blocos?.length === 0 && (
          <div className="text-center p-8 text-slate-500 border border-dashed border-slate-700 rounded-xl">
            Nenhum bloco de horário para hoje.
          </div>
        )}
      </div>
    </div>
  )
}

function BadgeStatus({ status }: { status: string }) {
  const map: Record<string, { c: string, l: string }> = {
    rascunho: { c: 'badge-gray', l: 'Rascunho' },
    ativo: { c: 'badge-green', l: 'Em Andamento' },
    encerrado: { c: 'badge-blue', l: 'Aguardando Aprovação' },
    aprovado: { c: 'badge-green', l: 'Dia Aprovado' },
  }
  const t = map[status] || map.rascunho
  return <span className={`badge ${t.c}`}>{t.l}</span>
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
