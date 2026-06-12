import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      redirect: '/worlds',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/worlds',
      name: 'worlds',
      component: () => import('@/views/WorldListView.vue'),
    },
    {
      path: '/worlds/create',
      name: 'world-create',
      component: () => import('@/views/WorldFormView.vue'),
    },
    {
      path: '/worlds/:id',
      name: 'world-detail',
      component: () => import('@/views/WorldDetailView.vue'),
    },
    {
      path: '/worlds/:id/edit',
      name: 'world-edit',
      component: () => import('@/views/WorldFormView.vue'),
    },
    {
      path: '/worlds/:worldId/characters/create',
      name: 'character-create',
      component: () => import('@/views/CharacterFormView.vue'),
    },
    {
      path: '/characters/:id/edit',
      name: 'character-edit',
      component: () => import('@/views/CharacterFormView.vue'),
    },
    {
      path: '/chat/:conversationId',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (!to.meta.guest && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guest && auth.isAuthenticated) {
    return { name: 'worlds' }
  }
})

export default router
