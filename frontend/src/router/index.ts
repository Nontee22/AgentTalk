import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/worlds',
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
  ],
})

export default router
