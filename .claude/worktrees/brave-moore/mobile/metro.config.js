const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

/**
 * Metro configuration
 * https://facebook.github.io/metro/docs/configuration
 */
const config = {
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
  resolver: {
    alias: {
      '@': './src',
      '@components': './src/components',
      '@screens': './src/screens',
      '@navigation': './src/navigation',
      '@services': './src/services',
      '@store': './src/store',
      '@utils': './src/utils',
      '@types': './src/types',
      '@hooks': './src/hooks',
      '@constants': './src/constants',
    },
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);