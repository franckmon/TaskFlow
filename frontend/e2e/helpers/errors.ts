import { Page } from '@playwright/test';

export async function abortApiRoute(page: Page, pathPattern: string) {
  await page.route(pathPattern, (route) => route.abort('connectionrefused'));
}

export async function delayApiRoute(
  page: Page,
  pathPattern: string,
  delayMs: number,
  options: { methods?: string[] } = {},
) {
  const methods = options.methods ?? ['GET', 'POST'];

  await page.route(pathPattern, async (route) => {
    if (methods.includes(route.request().method())) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }

    await route.continue();
  });
}

export async function delayTasksFetchAfterLogin(page: Page, delayMs: number) {
  const gate = { enabled: false };

  await page.route('**/tasks**', async (route) => {
    if (route.request().method() === 'GET' && gate.enabled) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }

    await route.continue();
  });

  return {
    enable() {
      gate.enabled = true;
    },
  };
}
