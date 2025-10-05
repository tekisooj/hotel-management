import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import globals from 'globals'
import vueParser from 'vue-eslint-parser'

const nuxtGlobals = {
  defineNuxtConfig: 'readonly',
  defineNuxtPlugin: 'readonly',
  defineNuxtRouteMiddleware: 'readonly',
  useRuntimeConfig: 'readonly',
  navigateTo: 'readonly',
  $fetch: 'readonly',
  process: 'readonly',
  URL: 'readonly',
}

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  pluginVue.configs['flat/essential'],
  {
    ignores: ['.nuxt/**', 'dist/**', '.output/**', 'node_modules/**'],
  },
  {
    files: ['**/*.{ts,js,vue}'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        ecmaVersion: 'latest',
        sourceType: 'module',
        extraFileExtensions: ['.vue'],
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...nuxtGlobals,
      },
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-empty-object-type': 'off',
    },
  }
)
