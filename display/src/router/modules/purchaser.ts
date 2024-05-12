export default {
  path: "/purchaser",
  redirect: "/purchaser/data",
  meta: {
    icon: "ep:user-filled",
    title: "招标人",
    rank: 10,
    showLink: true
  },
  children: [
    {
      path: "/purchaser/data",
      name: "PurchaserData",
      component: () => import("@/views/placeholder/index.vue"),
      meta: {
        title: "数据"
      }
    },
    {
      path: "/purchaser/analyze",
      name: "PurchaserAnalyze",
      component: () => import("@/views/placeholder/index.vue"),
      meta: {
        title: "分析"
      }
    }
  ]
} satisfies RouteConfigsTable;
