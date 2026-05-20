/**
 * Hook para conexão e escuta de eventos via WebSocket (Django Channels).
 * Passa o JWT Token via query string para autenticação.
 */
import { useEffect, useRef } from 'react'
import { useAuthStore } from '../store/authStore'
import { useQueryClient } from '@tanstack/react-query'

export function useWebSocket() {
  const { accessToken, usuario } = useAuthStore()
  const queryClient = useQueryClient()
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!accessToken || !usuario) return

    // Conecta no endpoint apropriado com base no perfil (BU ou User puro)
    const endpoint = usuario.perfil === 'lider' || usuario.perfil === 'admin'
      ? `/ws/bu/${usuario.bu_id}/?token=${accessToken}`
      : `/ws/user/${usuario.id}/?token=${accessToken}`
      
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${endpoint}`

    ws.current = new WebSocket(wsUrl)

    ws.current.onopen = () => {
      console.log('✅ WebSocket Conectado')
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'agendas.update':
            // Invalida cache de agendas ao receber atualização da BU
            queryClient.invalidateQueries({ queryKey: ['agendas_bu'] })
            break
          case 'notificacao.push':
            // Emite notificação push nativa do navegador
            if (Notification.permission === 'granted') {
              new Notification(data.title, { body: data.message })
            }
            queryClient.invalidateQueries({ queryKey: ['notificacoes'] })
            break
          default:
            console.log('Evento WS não tratado:', data)
        }
      } catch (err) {
        console.error('Erro ao processar mensagem WS', err)
      }
    }

    ws.current.onclose = () => {
      console.log('❌ WebSocket Desconectado')
    }

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [accessToken, usuario, queryClient])

  return ws.current
}
