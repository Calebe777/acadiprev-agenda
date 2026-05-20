import api from './client'

// ---- Auth ----
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/token/', { email, password }),
  refresh: (refresh: string) =>
    api.post('/auth/token/refresh/', { refresh }),
  logout: (refresh: string) =>
    api.post('/auth/token/blacklist/', { refresh }),
}

// ---- Tenant ----
export const tenantApi = {
  config: () => api.get('/tenant/config/'),
}

// ---- Agendas ----
export const agendaApi = {
  hoje: () => api.get('/agendas/hoje/'),
  porData: (data: string) => api.get(`/agendas/data/${data}/`),
  criar: (payload: object) => api.post('/agendas/', payload),
  checkin: (id: string) => api.patch(`/agendas/${id}/checkin/`),
  checkout: (id: string, resumo: string) =>
    api.patch(`/agendas/${id}/checkout/`, { resumo_final: resumo }),
  porBU: (buId: string, data: string) => api.get(`/agendas/bu/${buId}/?data=${data}`),
}

// ---- Blocos ----
export const blocoApi = {
  listar: (agendaId: string) => api.get(`/agendas/${agendaId}/blocos/`),
  criar: (agendaId: string, payload: object) =>
    api.post(`/agendas/${agendaId}/blocos/`, payload),
  atualizar: (id: string, payload: object) => api.put(`/blocos/${id}/`, payload),
  remover: (id: string) => api.delete(`/blocos/${id}/`),
  iniciar: (id: string) => api.patch(`/blocos/${id}/iniciar/`),
  concluir: (id: string, formData: FormData) =>
    api.patch(`/blocos/${id}/concluir/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  redistribuir: (id: string, payload: object) =>
    api.patch(`/blocos/${id}/redistribuir/`, payload),
}

// ---- Tarefas / Kanban ----
export const tarefaApi = {
  listar: (params?: Record<string, string>) => api.get('/tarefas/', { params }),
  criar: (payload: object) => api.post('/tarefas/', payload),
  detalhe: (id: string) => api.get(`/tarefas/${id}/`),
  atualizar: (id: string, payload: object) => api.put(`/tarefas/${id}/`, payload),
  deletar: (id: string) => api.delete(`/tarefas/${id}/`),
  mover: (id: string, status: string, ordem: number) =>
    api.patch(`/tarefas/${id}/mover/`, { status, ordem_kanban: ordem }),
  reordenar: (tarefas: Array<{ id: string; status: string; ordem_kanban: number }>) =>
    api.patch('/tarefas/reordenar/', { tarefas }),
  vincularBloco: (id: string, blocoId: string) =>
    api.patch(`/tarefas/${id}/vincular-bloco/`, { bloco_id: blocoId }),
  desvincular: (id: string) => api.patch(`/tarefas/${id}/desvincular/`),
  porBU: (buId: string) => api.get(`/tarefas/bu/${buId}/`),
  atribuir: (payload: object) => api.post('/tarefas/atribuir/', payload),
}

// ---- Justificativas ----
export const justificativaApi = {
  listar: () => api.get('/justificativas/'),
  criar: (payload: object) => api.post('/justificativas/', payload),
  pendentes: () => api.get('/justificativas/pendentes/'),
  avaliar: (id: string, payload: object) =>
    api.patch(`/justificativas/${id}/avaliar/`, payload),
  historico: (params?: object) => api.get('/justificativas/historico/', { params }),
}

// ---- Setor Config ----
export const setorConfigApi = {
  minhaBU: () => api.get('/setor-config/minha-bu/'),
  atualizar: (buId: string, payload: object) =>
    api.put(`/setor-config/${buId}/`, payload),
}

// ---- Notificações ----
export const notificacaoApi = {
  listar: (apenasNaoLidas = false) =>
    api.get('/notificacoes/', { params: { nao_lidas: apenasNaoLidas } }),
  marcarLida: (id: string) => api.patch(`/notificacoes/${id}/lida/`),
  marcarTodasLidas: () => api.post('/notificacoes/marcar-todas-lidas/'),
}

// ---- Relatórios ----
export const relatorioApi = {
  meuDesempenho: (periodo = 'semana') =>
    api.get('/relatorios/meu-desempenho/', { params: { periodo } }),
  frequencia: (params: object) => api.get('/relatorios/frequencia/', { params }),
  bu: (params: object) => api.get('/relatorios/bu/', { params }),
  executivo: () => api.get('/relatorios/executivo/'),
  exportar: (payload: object) => api.post('/relatorios/exportar/', payload),
  statusExportacao: (taskId: string) => api.get(`/relatorios/exportar/${taskId}/`),
}

// ---- Admin ----
export const adminApi = {
  usuarios: {
    listar: (params?: object) => api.get('/admin/usuarios/', { params }),
    criar: (payload: object) => api.post('/admin/usuarios/', payload),
    atualizar: (id: string, payload: object) =>
      api.put(`/admin/usuarios/${id}/`, payload),
    deletar: (id: string) => api.delete(`/admin/usuarios/${id}/`),
  },
  bus: {
    listar: () => api.get('/admin/bus/'),
    criar: (payload: object) => api.post('/admin/bus/', payload),
    atualizar: (id: string, payload: object) =>
      api.put(`/admin/bus/${id}/`, payload),
    membros: (id: string) => api.get(`/admin/bus/${id}/membros/`),
  },
  feriados: {
    listar: () => api.get('/admin/feriados/'),
    criar: (payload: object) => api.post('/admin/feriados/', payload),
    atualizar: (id: string, payload: object) =>
      api.put(`/admin/feriados/${id}/`, payload),
  },
  templates: {
    listar: () => api.get('/admin/templates/'),
    criar: (payload: object) => api.post('/admin/templates/', payload),
  },
}
