// Buffer polyfill for browser environment
export const Buffer = {
  from: () => [],
  alloc: () => [],
  isBuffer: () => false,
  concat: () => [],
  byteLength: () => 0
};

export default Buffer;