// Re-export all types
export * from './financial';
export * from './analytics';

// Common utility types
export type Optional<T, K extends keyof T> = Pick<Partial<T>, K> & Omit<T, K>;

export type Nullable<T> = T | null;

export type AsyncState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

export type FormStepProps<T = any> = {
  data: T;
  onNext: (data: T) => void;
  onPrev: () => void;
  isValid?: boolean;
  errors?: Record<string, string>;
};