// 模拟后端动态生成路由
import { defineFakeRoute } from "vite-plugin-fake-server/client";

/**
 * roles：页面级别权限，这里模拟二种 "admin"、"common"
 * admin：管理员角色
 * common：普通角色
 */
const permissionRouter = {
  path: "/permission",
  meta: {
    title: "权限管理",
    icon: "ep:lollipop",
    rank: 10,
    showLink: false,
  },
  children: [
    {
      path: "/permission/page/index",
      name: "PermissionPage",
      meta: {
        title: "页面权限",
        roles: ["admin", "common"]
      }
    },
    {
      path: "/permission/button/index",
      name: "PermissionButton",
      meta: {
        title: "按钮权限",
        roles: ["admin", "common"],
        auths: [
          "permission:btn:add",
          "permission:btn:edit",
          "permission:btn:delete"
        ]
      }
    }
  ]
};

const districtCodes = [
  [450100, ["南宁市", "NanNing"]],
  [450200, ["柳州市", "LiuZhou"]],
  [450300, ["桂林市", "GuiLin"]],
  [450400, ["梧州市", "WuZhou"]],
  [450500, ["北海市", "BeiHai"]],
  [450600, ["防城港市", "FangChengGang"]],
  [450700, ["钦州市", "QinZhou"]],
  [450800, ["贵港市", "GuiGang"]],
  [450900, ["玉林市", "YuLin"]],
  [451000, ["百色市", "BaiSe"]],
  [451100, ["贺州市", "HeZhou"]],
  [451200, ["河池市", "HeChi"]],
  [451300, ["来宾市", "LaiBin"]],
  [451400, ["崇左市", "ConZuo"]]
];

const districtRoutes = {
  path: "/district",
  redirect: "/district/about",
  meta: {
    icon: "ep:location-filled",
    title: "地区",
    rank: 10,
    showLink: true
  },
  children: [
    {
      path: "/district/about",
      name: "DistrictAbout",
      component: "district/about/DistrictAbout",
      meta: {
        title: "总览"
      }
    },
    {
      path: "/district/city",
      name: "DistrictCity",
      meta: {
        title: "市级"
      },
      children: districtCodes.map(district => {
        const name = `District${district[1][1]}`;
        return {
          path: `/${district[0]}`,
          name: name,
          component: `district/city/${name}`,
          meta: {
            title: district[1][0]
          }
        };
      })
    }
  ]
};


export default defineFakeRoute([
  {
    url: "/get-async-routes",
    method: "get",
    response: () => {
      return {
        success: true,
        data: [permissionRouter, districtRoutes]
      };
    }
  }
]);
