/**
 * Хук для работы с Telegram Web App API.
 * Возвращает null-safe значения — безопасно использовать и в браузере, и в Telegram.
 */

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
}

export interface TelegramWebApp {
  ready: () => void;
  expand: () => void;
  close: () => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  enableClosingConfirmation: () => void;
  initData: string;
  initDataUnsafe: {
    user?: TelegramUser;
    auth_date?: number;
    hash?: string;
  };
  colorScheme: 'light' | 'dark';
  BackButton: {
    isVisible: boolean;
    show: () => void;
    hide: () => void;
    onClick: (fn: () => void) => void;
    offClick: (fn: () => void) => void;
  };
  MainButton: {
    text: string;
    isVisible: boolean;
    isActive: boolean;
    show: () => void;
    hide: () => void;
    enable: () => void;
    disable: () => void;
    setText: (text: string) => void;
    onClick: (fn: () => void) => void;
    showProgress: (leaveActive: boolean) => void;
    hideProgress: () => void;
  };
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
    selectionChanged: () => void;
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

export function useTelegram() {
  const tg: TelegramWebApp | null = window.Telegram?.WebApp ?? null;
  const isInTelegram = !!tg && !!tg.initData;
  const tgUser: TelegramUser | null = tg?.initDataUnsafe?.user ?? null;
  const initData: string = tg?.initData ?? '';

  const haptic = {
    success: () => tg?.HapticFeedback.notificationOccurred('success'),
    error:   () => tg?.HapticFeedback.notificationOccurred('error'),
    tap:     () => tg?.HapticFeedback.impactOccurred('light'),
  };

  return { tg, isInTelegram, tgUser, initData, haptic };
}
