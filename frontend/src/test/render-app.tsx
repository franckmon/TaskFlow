import { RenderResult } from '@testing-library/react';
import { ReactElement } from 'react';
import App from '../App';
import { renderWithAuth } from './utils/renderWithAuth';

export function renderApp(): RenderResult {
  return renderWithAuth(<App />, { withSessionInitializer: true });
}

export function renderIntegration(ui: ReactElement): RenderResult {
  return renderWithAuth(ui, { withSessionInitializer: true });
}
