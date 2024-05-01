export default {
  path: "/district",
  redirect: "/district/data",
  meta: {
    icon: "ep:location-filled",
    title: "地区",
    rank: 10,
    showLink: true
  },
  children: [
    {
      path: "/district/data",
      name: "DistrictData",
      component: () => import("@/views/placeholder/index.vue"),
      meta: {
        title: "数据"
      }
    },
    {
      path: "/district/analyze",
      name: "DistrictAnalyze",
      component: () => import("@/views/placeholder/index.vue"),
      meta: {
        title: "分析"
      }
    }
  ]
} satisfies RouteConfigsTable;
