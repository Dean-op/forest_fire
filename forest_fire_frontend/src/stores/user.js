import { defineStore } from 'pinia'
import api from '../api'

export const useUserStore = defineStore('user', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        user: JSON.parse(localStorage.getItem('user')) || null
    }),
    getters: {
        isLoggedIn: (state) => !!state.token,
        role: (state) => state.user?.role || ''
    },
    actions: {
        async login(username, password) {
            // OAuth2 requires form data
            const formData = new URLSearchParams()
            formData.append('username', username)
            formData.append('password', password)

            const res = await api.post('/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            })
            this.token = res.access_token
            localStorage.setItem('token', this.token)
            await this.fetchUser()
        },
        async fetchUser() {
            const user = await api.get('/auth/me')
            this.user = user
            localStorage.setItem('user', JSON.stringify(user))
        },
        logout() {
            this.token = ''
            this.user = null
            localStorage.removeItem('token')
            localStorage.removeItem('user')
        }
    }
})
