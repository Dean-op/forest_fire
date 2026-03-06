import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        component: MainLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'Dashboard',
                component: () => import('../views/Dashboard.vue')
            },
            {
                path: 'tasks',
                name: 'Tasks',
                component: () => import('../views/Tasks.vue'),
                meta: { roles: ['operator', 'admin'] }
            },
            {
                path: 'history',
                name: 'History',
                component: () => import('../views/History.vue'),
                meta: { roles: ['operator', 'admin'] }
            },
            {
                path: 'stats',
                name: 'Stats',
                component: () => import('../views/Stats.vue'),
                meta: { roles: ['supervisor', 'admin'] }
            },
            {
                path: 'cameras',
                name: 'Cameras',
                component: () => import('../views/Cameras.vue'),
                meta: { roles: ['supervisor', 'admin'] }
            },
            {
                path: 'shift-logs',
                name: 'ShiftLogs',
                component: () => import('../views/ShiftLogs.vue'),
                meta: { roles: ['supervisor', 'admin'] }
            },
            {
                path: 'notices',
                name: 'NoticeBoard',
                component: () => import('../views/NoticeBoard.vue'),
                meta: { roles: ['operator', 'supervisor', 'admin'] }
            },
            {
                path: 'admin/users',
                name: 'UserManagement',
                component: () => import('../views/UserManagement.vue'),
                meta: { roles: ['admin'] }
            },
            {
                path: 'admin/config',
                name: 'SystemConfig',
                component: () => import('../views/SystemConfig.vue'),
                meta: { roles: ['admin'] }
            },
            {
                path: 'admin/announcements',
                name: 'Announcements',
                component: () => import('../views/Announcements.vue'),
                meta: { roles: ['admin'] }
            },
            {
                path: 'admin/logs',
                name: 'SystemLogs',
                component: () => import('../views/SystemLogs.vue'),
                meta: { roles: ['admin'] }
            },
            {
                path: 'admin/backup',
                name: 'Backup',
                component: () => import('../views/Backup.vue'),
                meta: { roles: ['admin'] }
            },
            {
                path: 'profile',
                name: 'Profile',
                component: () => import('../views/Profile.vue')
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const userStore = useUserStore()

    if (to.meta.requiresAuth !== false && !userStore.isLoggedIn) {
        next({ name: 'Login' })
    } else if (to.name === 'Login' && userStore.isLoggedIn) {
        next({ name: 'Dashboard' })
    } else {
        // Basic role guard
        if (to.meta.roles && !to.meta.roles.includes(userStore.role)) {
            next({ name: 'Dashboard' }) // Redirect unauthorized
        } else {
            next()
        }
    }
})

export default router
