/**
 * RelatoriosPage — Relatórios e Exportação.
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Download, BarChart2, Calendar, FileText } from 'lucide-react'
import { relatorioApi } from '../api/endpoints'
import { useAuthStore } from '../store/authStore'

export default function RelatoriosPage() {
  const { usuario } = useAuthStore()
  const [periodo, setPeriodo] = useState('mes')

  const { data: desempenho, isLoading } = useQuery({
    queryKey: ['meu_desempenho', periodo],
    queryFn: () => relatorioApi.meuDesempenho(periodo).then(res => res.data),
  })

  const exportarMutation = useMutation({
    mutationFn: (tipo: string) => relatorioApi.exportar({ tipo, formato: 'pdf' }).then(res => res.data),
    onSuccess: (data) => {
      alert(`Exportação iniciada. Task ID: ${data.task_id}`)
    }
  })

  if (isLoading) return <div className="p-8 text-center text-slate-400">Carregando relatórios...</div>

  return (
    <div className="flex flex-col h-full gap-6 max-w-5xl mx-auto">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart2 size={24} className="text-purple-500" />
            Relatórios
          </h1>
          <p className="text-sm text-slate-400 mt-1">Acompanhe seu desempenho e métricas.</p>
        </div>

        <div className="flex gap-3">
          <select 
            className="input py-2 bg-slate-800"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
          >
            <option value="semana">Últimos 7 dias</option>
            <option value="mes">Este Mês</option>
          </select>

          {usuario?.perfil !== 'colaborador' && (
            <button 
              onClick={() => exportarMutation.mutate('frequencia')}
              className="btn-primary"
              disabled={exportarMutation.isPending}
            >
              <Download size={18} /> Exportar Frequência
            </button>
          )}
        </div>
      </header>

      {/* Resumo Pessoal */}
      <div className="card">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <FileText size={18} className="text-slate-400" /> Meu Desempenho
        </h2>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <MetricBox label="Blocos Planejados" value={desempenho?.resumo.total_blocos_planejados} />
          <MetricBox label="Concluídos" value={desempenho?.resumo.blocos_concluidos} color="text-green-400" />
          <MetricBox label="Parciais" value={desempenho?.resumo.blocos_parciais} color="text-yellow-400" />
          <MetricBox label="Não Realizados" value={desempenho?.resumo.blocos_nao_realizados} color="text-red-400" />
          <MetricBox label="Pontualidade Check-in" value={`${desempenho?.resumo.media_checkin_pontual}%`} color="text-blue-400" />
        </div>

        <div>
          <h3 className="text-sm font-medium text-slate-400 mb-3">Histórico Diário</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-800/50 text-slate-400">
                <tr>
                  <th className="px-4 py-2 font-medium rounded-l-lg">Data</th>
                  <th className="px-4 py-2 font-medium">Progresso</th>
                  <th className="px-4 py-2 font-medium text-right rounded-r-lg">Concluído</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {desempenho?.por_dia.map((dia: any) => (
                  <tr key={dia.data} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 flex items-center gap-2">
                      <Calendar size={14} className="text-slate-500" />
                      {new Date(dia.data).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-4 py-3 w-1/2">
                      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${dia.pct >= 80 ? 'bg-green-500' : dia.pct >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                          style={{ width: `${dia.pct}%` }} 
                        />
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-medium">
                      {dia.concluidos} / {dia.total} ({dia.pct}%)
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricBox({ label, value, color = "text-slate-100" }: { label: string, value: any, color?: string }) {
  return (
    <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex flex-col justify-center items-center text-center">
      <div className={`text-2xl font-bold ${color}`}>{value || 0}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}
