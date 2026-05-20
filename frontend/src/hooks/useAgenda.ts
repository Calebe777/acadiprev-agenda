/**
 * Hook para gerenciar as chamadas de agenda com react-query.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { agendaApi, blocoApi } from '../api/endpoints'

export function useAgenda(dataAtual: string) {
  const queryClient = useQueryClient()

  const agendaQuery = useQuery({
    queryKey: ['agenda', dataAtual],
    queryFn: () => agendaApi.porData(dataAtual).then((res) => res.data),
    retry: false,
  })

  const checkinMutation = useMutation({
    mutationFn: (id: string) => agendaApi.checkin(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agenda', dataAtual] }),
  })

  const checkoutMutation = useMutation({
    mutationFn: ({ id, resumo }: { id: string; resumo: string }) => agendaApi.checkout(id, resumo),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agenda', dataAtual] }),
  })

  const concluirBlocoMutation = useMutation({
    mutationFn: ({ id, formData }: { id: string; formData: FormData }) => blocoApi.concluir(id, formData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agenda', dataAtual] }),
  })

  return {
    agenda: agendaQuery.data,
    isLoading: agendaQuery.isLoading,
    isError: agendaQuery.isError,
    checkin: checkinMutation.mutateAsync,
    checkout: checkoutMutation.mutateAsync,
    concluirBloco: concluirBlocoMutation.mutateAsync,
    isMutating: checkinMutation.isPending || checkoutMutation.isPending || concluirBlocoMutation.isPending,
  }
}
