// Process polyfill for browser environment
export const process = {
  env: {},
  browser: true,
  version: 'v1.0.0',
  nextTick: (fn) => setTimeout(fn, 0)
};

export default process;