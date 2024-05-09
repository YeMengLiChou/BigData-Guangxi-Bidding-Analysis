const Layout = () => import("@/layout/index.vue");

export default {
  path: "/announcement",
  name: "Announcement",
  component: Layout,
  redirect: "/announcement/index",
  meta: {
    icon: "ep:trend-charts",
    title: "公告",
    rank: 0
  },
  children: [
    {
      path: "/stat",
      name: "AnnouncementStats",
      component: () => import("@/views/announcement/stats/index.vue"),
      meta: {
        title: "统计",
        showLink: true,
        showParent: true
      }
    },
    {
      path: "/records",
      name: "AnnouncementRecords",
      component: () => import("@/views/announcement/records/index.vue"),
      meta: {
        title: "公告数据记录",
        showLink: true,
        showParent: true
      }
    }
  ]
} satisfies RouteConfigsTable;
