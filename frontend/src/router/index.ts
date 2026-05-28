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
      component: () => import('@/views/HomeView.vue'),
    },
  ],
})

export default router
