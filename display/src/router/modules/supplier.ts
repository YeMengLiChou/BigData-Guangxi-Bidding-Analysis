
export default {
  path: "/supplier",
  redirect: "/supplier/data",
  meta: {
    icon: "ep:shop",
    title: "供应商",
    rank: 10,
    showLink: true
  },
  children: [
    {
      path: "/supplier/data",
      name: "SupllierData",
      component: () => import("@/views/placeholder/index.vue"),
      meta: {
        title: "数据"
      }
    },
    {
      path: "/supplier/analyze",
      name: "SupllierAnalyze",
      component: () => import("@/views/placeholder/index.vue"),
      meta: {
        title: "分析"
      }
    }
  ]
} satisfies RouteConfigsTable;
