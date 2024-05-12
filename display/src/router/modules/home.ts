const Layout = () => import("@/layout/index.vue");

export default {
  path: "/",
  name: "Home",
  component: Layout,
  redirect: "/home",
  meta: {
    icon: "ep:trend-charts",
    title: "概要",
    rank: 0,
  },
  children: [
    {
      path: "/home",
      name: "HomeIndex",
      component: () => import("@/views/home/index.vue"),
      meta: {
        title: "概要",
        keepAlive: true,
        showLink: true,
        showParent: true,
      }
    }
  ]
} satisfies RouteConfigsTable;
