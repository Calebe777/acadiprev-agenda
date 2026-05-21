/**
 * DashboardPage — tela inicial corporativa premium.
 *
 * Seções:
 *   1) Cabeçalho com saudação, data e ações rápidas
 *   2) KPI cards com indicadores visuais
 *   3) Linha do tempo hora a hora + gráfico de produtividade semanal
 *   4) Atividades recentes e tarefas urgentes
 *
 * Dados mockados em `mock*` — substituir pelos endpoints reais nos TODOs.
 */
import { useMemo, useState } from 'react'
import {
  CheckCircle2, Clock, AlertTriangle, ListChecks,
  PlayCircle, Plus, TrendingUp, TrendingDown,
  ArrowRight, Flame, Zap,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import TarefaModal from '../components/TarefaModal'

// ============================================================
// Tipos
// ============================================================
type KpiTone = 'primary' | 'success' | 'warning' | 'danger'

interface Kpi {
  label: string
  value: number | string
  subtext?: string
  change?: number       // % mudança vs ontem (positivo = bom)
  tone: KpiTone
  icon: typeof CheckCircle2
  progress?: number     // 0-100, ring visual
}

interface BlocoTimeline {
  hora: string
  titulo?: string
  status?: 'planejado' | 'em_andamento' | 'concluido' | 'atrasado'
  setor?: string
  duracao?: number   // minutos
}

interface Atividade {
  id: number
  tipo: 'checkin' | 'concluido' | 'tarefa' | 'alerta'
  texto: string
  tempo: string
  usuario: string
}

// ============================================================
// MOCK DATA
// ============================================================
const mockKpis: Kpi[] = [
  { label: 'Tarefas de hoje',  value: 14, subtext: '10 ativas',       change: 17,  tone: 'primary', icon: ListChecks,   progress: 57 },
  { label: 'Em andamento',     value: 5,  subtext: '3 com prazo hoje', change: -10, tone: 'warning', icon: PlayCircle,   progress: 36 },
  { label: 'Concluídas',       value: 8,  subtext: 'Meta: 12',        change: 25,  tone: 'success', icon: CheckCircle2, progress: 67 },
  { label: 'Atrasadas',        value: 2,  subtext: 'Ação necessária',  change: -33, tone: 'danger',  icon: AlertTriangle, progress: 14 },
]

const mockTimeline: BlocoTimeline[] = (() => {
  const exemplo: Record<number, Partial<BlocoTimeline>> = {
    8:  { titulo: 'Daily de equipe',           status: 'concluido',    setor: 'Operações', duracao: 60 },
    9:  { titulo: 'Revisar processos do RH',   status: 'concluido',    setor: 'RH',        duracao: 45 },
    10: { titulo: 'Atendimento N1',            status: 'em_andamento', setor: 'Suporte',   duracao: 90 },
    11: { titulo: 'Relatório mensal',          status: 'atrasado',     setor: 'Financeiro',duracao: 60 },
    13: { titulo: 'Reunião de planejamento',   status: 'planejado',    setor: 'Diretoria', duracao: 60 },
    14: { titulo: 'Treinamento — onboarding',  status: 'planejado',    setor: 'RH',        duracao: 120 },
    16: { titulo: 'Validar fluxo de tickets',  status: 'planejado',    setor: 'TI',        duracao: 45 },
  }
  const slots: BlocoTimeline[] = []
  for (let h = 8; h <= 18; h++) {
    slots.push({ hora: `${String(h).padStart(2, '0')}:00`, ...exemplo[h] })
  }
  return slots
})()

const mockProdSemana = [
  { dia: 'Seg', planejadas: 14, concluidas: 12, pct: 86 },
  { dia: 'Ter', planejadas: 16, concluidas: 14, pct: 88 },
  { dia: 'Qua', planejadas: 13, concluidas: 13, pct: 100 },
  { dia: 'Qui', planejadas: 18, concluidas: 15, pct: 83 },
  { dia: 'Sex', planejadas: 15, concluidas: 8,  pct: 53 },
]

const mockAtividades: Atividade[] = [
  { id: 1, tipo: 'checkin',   texto: 'fez check-in',                  tempo: 'há 2h',    usuario: 'Ana Lima' },
  { id: 2, tipo: 'concluido', texto: 'concluiu "Relatório de RH"',    tempo: 'há 1h30',  usuario: 'Carlos M.' },
  { id: 3, tipo: 'tarefa',    texto: 'criou tarefa "Revisão LGPD"',   tempo: 'há 45min', usuario: 'Patricia D.' },
  { id: 4, tipo: 'alerta',    texto: 'bloco "Financeiro" em atraso',  tempo: 'há 20min', usuario: 'Sistema' },
  { id: 5, tipo: 'concluido', texto: 'concluiu "Daily de equipe"',    tempo: 'há 10min', usuario: 'Você' },
]

const mockTarefasUrgentes = [
  { id: 1, titulo: 'Aprovar relatório Q2', prazo: 'Hoje 17:00', prioridade: 'alta',  setor: 'Financeiro' },
  { id: 2, titulo: 'Revisar contratos fornecedores', prazo: 'Hoje 18:00', prioridade: 'alta', setor: 'Jurídico' },
  { id: 3, titulo: 'Enviar deck reunião', prazo: 'Amanhã 09:00', prioridade: 'media', setor: 'Diretoria' },
]

// ============================================================
// Helpers
// ============================================================
function saudacao(nome?: string): string {
  const h = new Date().getHours()
  const c = h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite'
  const primeiro = nome?.split(' ')[0] ?? ''
  return primeiro ? `${c}, ${primeiro}!` : c
}

function dataLonga(): string {
  return new Intl.DateTimeFormat('pt-BR', {
    weekday: 'long', day: '2-digit', month: 'long', year: 'numeric',
  }).format(new Date())
}

function toneColor(tone: KpiTone): string {
  switch (tone) {
    case 'success': return 'var(--color-success)'
    case 'warning': return 'var(--color-warning)'
    case 'danger':  return 'var(--color-danger)'
    default:        return 'var(--color-primary)'
  }
}

// ============================================================
// KPI Card com ring de progresso
// ============================================================
function KpiCard({ kpi }: { kpi: Kpi }) {
  const color = toneColor(kpi.tone)
  const r = 20
  const circ = 2 * Math.PI * r
  const dash = ((kpi.progress ?? 0) / 100) * circ
  const isPositiveChange = (kpi.change ?? 0) >= 0
  const toneIsGoodWhenUp = kpi.tone === 'primary' || kpi.tone === 'success'
  const changeGood = toneIsGoodWhenUp ? isPositiveChange : !isPositiveChange

  return (
    <div className="card card-hover" style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            {kpi.label}
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.03em', lineHeight: 1.1, marginTop: 8 }}>
            {kpi.value}
          </div>
          {kpi.subtext && (
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
              {kpi.subtext}
            </div>
          )}
        </div>

        {/* Ring SVG */}
        <div style={{ position: 'relative', width: 52, height: 52 }}>
          <svg width="52" height="52" viewBox="0 0 52 52">
            <circle cx="26" cy="26" r={r} fill="none" stroke={`color-mix(in srgb, ${color} 14%, transparent)`} strokeWidth="4" />
            <circle
              cx="26" cy="26" r={r}
              fill="none"
              stroke={color}
              strokeWidth="4"
              strokeDasharray={`${dash} ${circ}`}
              strokeLinecap="round"
              transform="rotate(-90 26 26)"
              style={{ transition: 'stroke-dasharray 0.6s ease' }}
            />
          </svg>
          <div style={{
            position: 'absolute', inset: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color,
          }}>
            <kpi.icon size={18} />
          </div>
        </div>
      </div>

      {kpi.change !== undefined && (
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          fontSize: 12, fontWeight: 500,
          color: changeGood ? 'var(--color-success)' : 'var(--color-danger)',
          background: changeGood ? 'color-mix(in srgb, var(--color-success) 10%, transparent)' : 'color-mix(in srgb, var(--color-danger) 10%, transparent)',
          padding: '3px 8px',
          borderRadius: 999,
          width: 'fit-content',
        }}>
          {isPositiveChange ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {Math.abs(kpi.change)}% vs ontem
        </div>
      )}
    </div>
  )
}

// ============================================================
// Timeline
// ============================================================
const STATUS_COLORS: Record<string, string> = {
  concluido:    'var(--color-success)',
  em_andamento: 'var(--color-primary)',
  atrasado:     'var(--color-danger)',
  planejado:    'var(--color-text-muted)',
}

const STATUS_LABELS: Record<string, string> = {
  concluido: 'Concluído', em_andamento: 'Em andamento', atrasado: 'Atrasado', planejado: 'Planejado',
}

const STATUS_BADGE: Record<string, string> = {
  concluido: 'badge badge-success', em_andamento: 'badge badge-info', atrasado: 'badge badge-danger', planejado: 'badge badge-muted',
}

function Timeline({ blocos }: { blocos: BlocoTimeline[] }) {
  const horaAtual = new Date().getHours()
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '18px 22px', borderBottom: '1px solid var(--color-border)',
      }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text)' }}>Agenda de hoje</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>Linha do tempo hora a hora</div>
        </div>
        <button className="btn-primary" type="button" style={{ fontSize: 13, padding: '6px 12px' }}>
          <Plus size={14} /> Novo bloco
        </button>
      </div>

      <div style={{ maxHeight: 420, overflowY: 'auto' }}>
        {blocos.map((b) => {
          const h = parseInt(b.hora.split(':')[0], 10)
          const isNow = h === horaAtual
          const isPast = h < horaAtual
          return (
            <div key={b.hora} style={{
              display: 'grid',
              gridTemplateColumns: '70px 1fr',
              alignItems: 'stretch',
              borderTop: '1px solid var(--color-border)',
              background: isNow ? 'color-mix(in srgb, var(--color-primary) 5%, transparent)' : 'transparent',
              transition: 'background 0.15s',
            }}>
              {/* Hora */}
              <div style={{
                padding: '14px 12px',
                fontSize: 12, fontWeight: 600,
                color: isNow ? 'var(--color-primary)' : isPast ? 'var(--color-text-muted)' : 'var(--color-text-secondary)',
                borderRight: '2px solid ' + (isNow ? 'var(--color-primary)' : 'var(--color-border)'),
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4,
                opacity: isPast && !b.titulo ? 0.5 : 1,
              }}>
                {b.hora}
                {isNow && <span className="pulse-dot" />}
              </div>

              {/* Conteúdo */}
              <div style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 12, minHeight: 52 }}>
                {b.titulo ? (
                  <>
                    <div style={{
                      width: 3, alignSelf: 'stretch', borderRadius: 2,
                      background: STATUS_COLORS[b.status ?? 'planejado'] ?? 'var(--color-border)',
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: 13, fontWeight: 600, color: 'var(--color-text)',
                        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                      }}>
                        {b.titulo}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
                        {b.setor}{b.duracao ? ` · ${b.duracao}min` : ''}
                      </div>
                    </div>
                    <span className={STATUS_BADGE[b.status ?? 'planejado'] ?? 'badge badge-muted'}>
                      {STATUS_LABELS[b.status ?? 'planejado']}
                    </span>
                  </>
                ) : (
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                    {isPast ? '—' : 'Sem bloco programado'}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ============================================================
// Gráfico de barras da semana
// ============================================================
function ProdutividadeChart({ data }: { data: typeof mockProdSemana }) {
  const max = Math.max(...data.map(d => d.planejadas), 1)
  const today = new Date().getDay() // 0=dom, 1=seg...
  const diaIdx = today >= 1 && today <= 5 ? today - 1 : -1

  const totals = useMemo(() => {
    const c = data.reduce((a, d) => a + d.concluidas, 0)
    const p = data.reduce((a, d) => a + d.planejadas, 0)
    return { c, p, pct: p ? Math.round((c / p) * 100) : 0 }
  }, [data])

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '18px 22px', borderBottom: '1px solid var(--color-border)',
      }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text)' }}>Produtividade</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>Semana atual</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.03em' }}>
            {totals.pct}%
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            {totals.c}/{totals.p} concluídas
          </div>
        </div>
      </div>

      <div style={{ padding: '20px 22px 12px' }}>
        {/* Barras */}
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 140, marginBottom: 8 }}>
          {data.map((d, i) => {
            const isToday = i === diaIdx
            const heightPlan = (d.planejadas / max) * 120
            const heightConc = (d.concluidas / max) * 120
            const pctColor = d.pct >= 80 ? 'var(--color-success)' : d.pct >= 60 ? 'var(--color-warning)' : 'var(--color-danger)'
            return (
              <div key={d.dia} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: pctColor }}>{d.pct}%</div>
                <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 120, width: '100%' }}>
                  {/* barra planejadas */}
                  <div style={{
                    flex: 1,
                    height: heightPlan,
                    background: isToday ? 'color-mix(in srgb, var(--color-primary) 25%, transparent)' : 'var(--color-border)',
                    borderRadius: '4px 4px 0 0',
                    transition: 'height 0.4s ease',
                  }} />
                  {/* barra concluídas */}
                  <div style={{
                    flex: 1,
                    height: heightConc,
                    background: isToday ? 'var(--color-primary)' : pctColor,
                    borderRadius: '4px 4px 0 0',
                    opacity: isToday ? 1 : 0.75,
                    transition: 'height 0.4s ease',
                  }} />
                </div>
                <div style={{
                  fontSize: 12, fontWeight: isToday ? 700 : 500,
                  color: isToday ? 'var(--color-primary)' : 'var(--color-text-muted)',
                }}>
                  {d.dia}
                </div>
              </div>
            )
          })}
        </div>

        {/* Legenda */}
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--color-border)', display: 'inline-block' }} />
            Planejadas
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--color-primary)', display: 'inline-block' }} />
            Concluídas
          </span>
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Feed de atividades recentes
// ============================================================
const ATIV_ICON: Record<Atividade['tipo'], React.ReactNode> = {
  checkin:   <Zap size={13} />,
  concluido: <CheckCircle2 size={13} />,
  tarefa:    <Plus size={13} />,
  alerta:    <AlertTriangle size={13} />,
}
const ATIV_COLOR: Record<Atividade['tipo'], string> = {
  checkin:   'var(--color-primary)',
  concluido: 'var(--color-success)',
  tarefa:    'var(--color-text-muted)',
  alerta:    'var(--color-danger)',
}

function FeedAtividades({ atividades }: { atividades: Atividade[] }) {
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text)' }}>Atividade recente</div>
        <button className="btn-ghost" type="button" style={{ fontSize: 12 }}>
          Ver tudo <ArrowRight size={12} />
        </button>
      </div>
      <div>
        {atividades.map((a, i) => (
          <div key={a.id} style={{
            display: 'flex', alignItems: 'flex-start', gap: 12,
            padding: '12px 22px',
            borderTop: i > 0 ? '1px solid var(--color-border)' : 'none',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: `color-mix(in srgb, ${ATIV_COLOR[a.tipo]} 14%, transparent)`,
              color: ATIV_COLOR[a.tipo],
            }}>
              {ATIV_ICON[a.tipo]}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, color: 'var(--color-text)' }}>
                <strong style={{ fontWeight: 600 }}>{a.usuario}</strong>{' '}
                <span style={{ color: 'var(--color-text-secondary)' }}>{a.texto}</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>{a.tempo}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================
// Tarefas urgentes
// ============================================================
const PRIO_STYLE: Record<string, { badge: string, dot: string }> = {
  alta:  { badge: 'badge badge-danger',  dot: 'var(--color-danger)' },
  media: { badge: 'badge badge-warning', dot: 'var(--color-warning)' },
  baixa: { badge: 'badge badge-muted',   dot: 'var(--color-text-muted)' },
}

function TarefasUrgentes({ tarefas }: { tarefas: typeof mockTarefasUrgentes }) {
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Flame size={16} style={{ color: 'var(--color-danger)' }} />
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text)' }}>Urgente / Pendente</div>
        </div>
        <button className="btn-ghost" type="button" style={{ fontSize: 12 }}>
          Ver kanban <ArrowRight size={12} />
        </button>
      </div>
      <div>
        {tarefas.map((t, i) => (
          <div key={t.id} style={{
            display: 'flex', alignItems: 'center', gap: 14,
            padding: '12px 22px',
            borderTop: i > 0 ? '1px solid var(--color-border)' : 'none',
          }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
              background: PRIO_STYLE[t.prioridade]?.dot ?? 'var(--color-text-muted)',
            }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 13, fontWeight: 600, color: 'var(--color-text)',
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}>{t.titulo}</div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
                {t.setor} · {t.prazo}
              </div>
            </div>
            <span className={PRIO_STYLE[t.prioridade]?.badge ?? 'badge badge-muted'}>
              {t.prioridade}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================
// Barra de progresso do dia
// ============================================================
function BarraProgressoDia() {
  const agora = new Date()
  const inicio = 8 * 60   // 08:00
  const fim = 18 * 60     // 18:00
  const atual = agora.getHours() * 60 + agora.getMinutes()
  const pct = Math.min(100, Math.max(0, ((atual - inicio) / (fim - inicio)) * 100))
  const concluidas = mockTimeline.filter(b => b.status === 'concluido').length
  const total = mockTimeline.filter(b => b.titulo).length

  return (
    <div className="card" style={{ padding: '14px 22px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <Clock size={16} style={{ color: 'var(--color-primary)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
          {agora.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </span>
        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          · {concluidas}/{total} blocos concluídos hoje
        </span>
      </div>
      <div style={{ flex: 1, minWidth: 120 }}>
        <div style={{ height: 6, background: 'var(--color-border)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${pct}%`,
            background: 'linear-gradient(90deg, var(--color-primary), var(--color-primary-light))',
            borderRadius: 3,
            transition: 'width 0.8s ease',
          }} />
        </div>
      </div>
      <div style={{ fontSize: 11, color: 'var(--color-text-muted)', flexShrink: 0 }}>
        {Math.round(pct)}% do dia trabalhado
      </div>
    </div>
  )
}

// ============================================================
// Página Principal
// ============================================================
export default function DashboardPage() {
  const usuario = useAuthStore((s: any) => s.usuario)
  const [_hoje] = useState(() => new Date().toISOString().split('T')[0])
  const [showTarefaModal, setShowTarefaModal] = useState(false)

  // TODO: substituir mocks pelos endpoints reais:
  // const { data: agendaHoje } = useQuery({ queryKey: ['agendaHoje'], queryFn: () => agendaApi.hoje().then(r => r.data) })
  // const { data: prodSemana } = useQuery({ queryKey: ['prodSemana'], queryFn: () => relatorioApi.meuDesempenho('semana').then(r => r.data) })

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1400, margin: '0 auto' }}>

      {/* ── Cabeçalho ── */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.03em' }}>
            {saudacao(usuario?.nome)}
          </h1>
          <div style={{ marginTop: 4, fontSize: 13, color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>
            {dataLonga()}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-secondary" type="button">
            <Clock size={14} />
            Marcar ponto
          </button>
          <button className="btn-primary" type="button" onClick={() => setShowTarefaModal(true)}>
            <Plus size={14} />
            Nova tarefa
          </button>
        </div>
      </div>

      {/* ── Barra de progresso do dia ── */}
      <BarraProgressoDia />

      {/* ── KPIs ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 14 }}>
        {mockKpis.map(k => <KpiCard key={k.label} kpi={k} />)}
      </div>

      {/* ── Timeline + Gráfico ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.45fr) minmax(0, 1fr)', gap: 14, alignItems: 'start' }}>
        <Timeline blocos={mockTimeline} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <ProdutividadeChart data={mockProdSemana} />
          <TarefasUrgentes tarefas={mockTarefasUrgentes} />
        </div>
      </div>

      {/* ── Feed ── */}
      <FeedAtividades atividades={mockAtividades} />

      {showTarefaModal && <TarefaModal onClose={() => setShowTarefaModal(false)} />}
    </div>
  )
}
