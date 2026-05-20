import { test, expect } from '@playwright/test';

test.describe('Fluxo Principal da Agenda', () => {
  // Configuração global para usar um subdomínio de tenant (ex: acadiprev.localhost)
  test.use({ baseURL: 'http://acadiprev.localhost:3000' });

  test('Deve logar, fazer check-in, iniciar e concluir bloco', async ({ page }) => {
    // 1. Login
    await page.goto('/login');
    // Espera que o tenant resolva as cores no client-side
    await page.waitForSelector('h1', { state: 'visible' });
    
    await page.fill('input[type="email"]', 'colaborador@acadiprev.test');
    await page.fill('input[type="password"]', 'senha123');
    await page.click('button[type="submit"]');

    // 2. Vai para a página da Agenda (Home)
    await page.waitForURL('/agenda');
    await expect(page.locator('h1')).toContainText('Minha Agenda');

    // 3. Fazer Check-in (se o botão existir, senão assume que já fez)
    const btnCheckin = page.locator('button:has-text("Fazer Check-in")');
    if (await btnCheckin.isVisible()) {
      await btnCheckin.click();
      // O botão deve sumir
      await expect(btnCheckin).toBeHidden();
    }

    // 4. Iniciar o primeiro bloco pendente
    const btnIniciar = page.locator('button:has-text("Iniciar")').first();
    if (await btnIniciar.isVisible()) {
      await btnIniciar.click();
      
      // O status deve mudar para "Em andamento" e surgir botão Concluir
      await expect(page.locator('span.pulse-dot')).toBeVisible();
      
      // 5. Concluir Bloco
      const btnConcluir = page.locator('button:has-text("Concluir")').first();
      await btnConcluir.click();

      // Modal
      await expect(page.locator('h2', { hasText: 'Concluir Atividade' })).toBeVisible();
      
      // Muda status pra parcial para exigir observação
      await page.selectOption('select', 'parcial');
      await page.fill('textarea', 'Concluído parcialmente por falta de sistema');
      
      // Submete modal
      await page.locator('button:has-text("Finalizar Bloco")').click();
      
      // Verifica se modal fechou e o card atualizou
      await expect(page.locator('h2', { hasText: 'Concluir Atividade' })).toBeHidden();
      await expect(page.locator('text=Parcial')).toBeVisible();
    }
  });
});
