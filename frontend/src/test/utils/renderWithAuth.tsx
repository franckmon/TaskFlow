import { ReactElement, ReactNode } from 'react';
import {
  render,
  renderHook,
  RenderHookOptions,
  RenderHookResult,
  RenderOptions,
  RenderResult,
} from '@testing-library/react';
import { AuthProvider } from '../../contexts/AuthContext';
import { AuthSessionInitializer, useAuth } from '../../hooks/useAuth';

export type AuthRenderOptions = {
  withSessionInitializer?: boolean;
};

export function AuthTestProviders({
  children,
  withSessionInitializer = false,
}: {
  children: ReactNode;
  withSessionInitializer?: boolean;
}) {
  return (
    <AuthProvider>
      {withSessionInitializer ? <AuthSessionInitializer /> : null}
      {children}
    </AuthProvider>
  );
}

function buildAuthWrapper(
  authOptions: AuthRenderOptions,
  UserWrapper?: React.ComponentType<{ children: ReactNode }>,
) {
  return function AuthWrapper({ children }: { children: ReactNode }) {
    const content = UserWrapper ? <UserWrapper>{children}</UserWrapper> : children;

    return (
      <AuthTestProviders withSessionInitializer={authOptions.withSessionInitializer}>
        {content}
      </AuthTestProviders>
    );
  };
}

/** Render UI wrapped in AuthProvider (and optional AuthSessionInitializer). */
export function renderWithAuth(
  ui: ReactElement,
  options?: RenderOptions & AuthRenderOptions,
): RenderResult {
  const { withSessionInitializer = false, wrapper: UserWrapper, ...renderOptions } =
    options ?? {};

  return render(ui, {
    wrapper: buildAuthWrapper({ withSessionInitializer }, UserWrapper),
    ...renderOptions,
  });
}

/** @deprecated Use renderWithAuth — kept for existing imports. */
export const renderWithAuthProvider = renderWithAuth;

export function renderHookWithAuth<Result, Props>(
  hook: (props: Props) => Result,
  options?: RenderHookOptions<Props> & AuthRenderOptions,
): RenderHookResult<Result, Props> {
  const { withSessionInitializer = false, wrapper: UserWrapper, ...hookOptions } =
    options ?? {};

  return renderHook(hook, {
    wrapper: buildAuthWrapper({ withSessionInitializer }, UserWrapper),
    ...hookOptions,
  });
}

/** @deprecated Use renderHookWithAuth — kept for existing imports. */
export const renderHookWithAuthProvider = renderHookWithAuth;

export function renderUseAuth(
  options?: Omit<RenderHookOptions<unknown>, 'wrapper'> & AuthRenderOptions,
): RenderHookResult<ReturnType<typeof useAuth>, unknown> {
  return renderHookWithAuth(() => useAuth(), options);
}
