import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
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
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  const isAuthenticated = !!token

  if (!to.meta.guest && !isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guest && isAuthenticated) {
    return { name: 'worlds' }
  }
})

export default router
