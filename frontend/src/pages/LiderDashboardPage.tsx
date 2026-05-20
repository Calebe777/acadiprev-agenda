/**
 * LiderDashboardPage — Painel de controle da Business Unit.
 * Mostra status das agendas do time e justificativas pendentes.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, AlertCircle, CheckCircle2, Clock, Calendar } from 'lucide-react'
import { agendaApi, justificativaApi } from '../api/endpoints'
import { useAuthStore } from '../store/authStore'

export default function LiderDashboardPage() {
  const { usuario } = useAuthStore()
  const queryClient = useQueryClient()
  const [hoje] = useState(() => new Date().toISOString().split('T')[0])
  const [dataSelecionada, setDataSelecionada] = useState(hoje)

  const buId = usuario?.bu_id

  // Agendas do time
  const { data: agendas = [], isLoading: loadAgendas } = useQuery({
    queryKey: ['agendas_bu', buId, dataSelecionada],
    queryFn: () => agendaApi.porBU(buId!, dataSelecionada).then(res => res.data),
    enabled: !!buId,
  })

  // Justificativas pendentes
  const { data: justificativas = [], isLoading: loadJustificativas } = useQuery({
    queryKey: ['justificativas_pendentes'],
    queryFn: () => justificativaApi.pendentes().then(res => res.data),
    enabled: !!buId,
  })

  const avaliarMutation = useMutation({
    mutationFn: ({ id, status, comment }: any) => justificativaApi.avaliar(id, { status, comentario_lider: comment }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['justificativas_pendentes'] }),
  })

  if (!buId) return <div className="p-8 text-center text-red-400">Você não possui uma Business Unit vinculada.</div>

  const online = agendas.filter((a: any) => a.check_in_at && !a.check_out_at).length
  const concluidas = agendas.filter((a: any) => a.status === 'aprovado' || a.status === 'encerrado').length

  return (
    <div className="flex flex-col h-full gap-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users size={24} className="text-blue-500" />
            Dashboard da Equipe
          </h1>
          <p className="text-sm text-slate-400 mt-1">Acompanhamento em tempo real da Business Unit.</p>
        </div>

        <div className="flex items-center gap-2">
          <Calendar size={16} className="text-slate-400" />
          <input 
            type="date" 
            className="input py-1.5 w-auto bg-slate-800"
            value={dataSelecionada}
            onChange={(e) => setDataSelecionada(e.target.value)}
          />
        </div>
      </header>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard title="Total da Equipe" value={agendas.length} icon={<Users size={20} />} />
        <KPICard title="Online Agora" value={online} icon={<div className="pulse-dot" />} />
        <KPICard title="Agendas Concluídas" value={concluidas} icon={<CheckCircle2 size={20} className="text-green-500" />} />
        <KPICard title="Justificativas" value={justificativas.length} icon={<AlertCircle size={20} className="text-orange-500" />} alert={justificativas.length > 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* Lista de Agendas */}
        <div className="lg:col-span-2 card flex flex-col min-h-0 p-0 overflow-hidden">
          <div className="p-4 border-b border-white/10 bg-slate-800/50">
            <h2 className="font-semibold text-lg">Status das Agendas</h2>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {loadAgendas ? (
              <div className="text-slate-400 text-center py-4">Carregando...</div>
            ) : agendas.length === 0 ? (
              <div className="text-slate-500 text-center py-8">Nenhuma agenda registrada para este dia.</div>
            ) : (
              <div className="grid gap-3">
                {agendas.map((agenda: any) => (
                  <div key={agenda.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-10 rounded-full ${agenda.check_in_at ? (agenda.check_out_at ? 'bg-blue-500' : 'bg-green-500') : 'bg-slate-600'}`} />
                      <div>
                        <div className="font-medium">{agenda.usuario_nome}</div>
                        <div className="text-xs text-slate-400 flex items-center gap-2">
                          <span className="flex items-center gap-1">
                            <Clock size={12} /> {agenda.check_in_at ? new Date(agenda.check_in_at).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'}) : 'Sem check-in'}
                          </span>
                          {agenda.blocos_pendentes > 0 && (
                            <span className="text-orange-400 bg-orange-400/10 px-1.5 py-0.5 rounded">
                              {agenda.blocos_pendentes} blocos pendentes
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-bold text-blue-400">{agenda.percentual_conclusao}%</div>
                        <div className="w-24 h-1.5 bg-slate-700 rounded-full mt-1 overflow-hidden">
                          <div className="h-full bg-blue-500" style={{ width: `${agenda.percentual_conclusao}%` }} />
                        </div>
                      </div>
                      <button className="btn-secondary py-1 px-2 text-xs">Ver Agenda</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Justificativas */}
        <div className="card flex flex-col min-h-0 p-0 overflow-hidden border-orange-500/20">
          <div className="p-4 border-b border-white/10 bg-orange-500/10">
            <h2 className="font-semibold text-lg text-orange-400 flex items-center gap-2">
              <AlertCircle size={18} /> Justificativas
            </h2>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {loadJustificativas ? (
              <div className="text-slate-400 text-center py-4">Carregando...</div>
            ) : justificativas.length === 0 ? (
              <div className="text-slate-500 text-center py-8">Tudo certo! Nenhuma justificativa pendente.</div>
            ) : (
              <div className="flex flex-col gap-3">
                {justificativas.map((j: any) => (
                  <div key={j.id} className="p-3 rounded-lg bg-slate-800 border border-slate-700">
                    <div className="font-medium text-sm mb-1">{j.colaborador.nome}</div>
                    <div className="text-xs text-slate-400 mb-2 bg-slate-900/50 p-1.5 rounded border border-slate-700/50">
                      Bloco: {j.bloco_detalhe.atividade} ({j.bloco_detalhe.horario_inicio})
                    </div>
                    <p className="text-sm italic text-slate-300 mb-3 border-l-2 border-slate-500 pl-2">
                      "{j.texto}"
                    </p>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => {
                          const c = prompt('Comentário (Aprovar):')
                          if(c) avaliarMutation.mutate({ id: j.id, status: 'aprovada', comment: c })
                        }}
                        className="flex-1 bg-green-500/20 text-green-400 hover:bg-green-500/30 text-xs py-1.5 rounded transition-colors"
                      >Aprovar</button>
                      <button 
                        onClick={() => {
                          const c = prompt('Motivo da Rejeição:')
                          if(c) avaliarMutation.mutate({ id: j.id, status: 'rejeitada', comment: c })
                        }}
                        className="flex-1 bg-red-500/20 text-red-400 hover:bg-red-500/30 text-xs py-1.5 rounded transition-colors"
                      >Rejeitar</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function KPICard({ title, value, icon, alert }: { title: string, value: string | number, icon: React.ReactNode, alert?: boolean }) {
  return (
    <div className={`card p-4 ${alert ? 'border-orange-500/50 bg-orange-500/5' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-slate-400">{title}</h3>
        <div className="text-slate-500">{icon}</div>
      </div>
      <div className={`text-3xl font-bold ${alert ? 'text-orange-400' : 'text-slate-100'}`}>{value}</div>
    </div>
  )
}
