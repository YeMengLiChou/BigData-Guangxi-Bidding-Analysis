import { BaseInfoVO } from "./types";
import { BaseInfo } from "@/api/base";
import Files from "@iconify-icons/ep/files";
import CircleCheck from "@iconify-icons/ep/circle-check";
import Money from "@iconify-icons/ep/money";
import Shop from "@iconify-icons/ep/shopping-trolley";

/**
 * 转换api数据为vo
 */
export const transformBaseInfoVO = (data: BaseInfo): Array<BaseInfoVO> => {
  const totalCountBaseInfo: BaseInfoVO = {
    name: "数据库公告数(条)",
    icon: Files,
    bgColor: "#fff5f4",
    color: "#e85f33",
    duration: 1800,
    value: data.announcementCount,
    data: data.announcementCountData
  };

  const transactionCountBaseInfo: BaseInfoVO = {
    name: "成交公告数(个)",
    icon: CircleCheck,
    bgColor: "#eff8f4",
    color: "#26ce83",
    duration: 1800,
    value: data.transactionsCount,
    data: data.transactionsCountData
  };
  const transactionVolumeBaseInfo: BaseInfoVO = {
    name: "成交总金额(¥)",
    icon: Money,
    bgColor: "#effaff",
    color: "#41b6ff",
    duration: 1800,
    value: data.transactionsVolume,
    data: data.transactionsVolumeData
  };

  // 供应商
  const supplierBaseInfo: BaseInfoVO = {
    name: "供应商统计个数",
    icon: Shop,
    bgColor: "#f6f4fe",
    color: "#7846e5",
    duration: 100,
    value: data.supplierCount,
    data: [data.supplierCount]
  };
  return [
    totalCountBaseInfo,
    transactionCountBaseInfo,
    transactionVolumeBaseInfo,
    supplierBaseInfo
  ];
};
