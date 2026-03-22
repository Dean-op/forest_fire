import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // 默认开启暗黑模式 (如果 localStorage 没设定，则默认为暗)
  const stored = localStorage.getItem('vue_theme')
  const isDark = ref(stored !== 'light')

  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  watch(isDark, (val) => {
    if (val) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('vue_theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('vue_theme', 'light')
    }
  }, { immediate: true })

  return { isDark, toggleTheme }
})
