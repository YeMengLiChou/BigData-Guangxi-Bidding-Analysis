import { BaseInfoVO } from "./types";
import { BaseInfo } from "@/api/base";

/**
 * 转换api数据为vo
 */
export const transformBaseInfoVO = (data: BaseInfo): Array<BaseInfoVO> => {
  const totalCountBaseInfo: BaseInfoVO = {
    name: "数据库公告数(条)",
    icon: "ep:office-building",
    bgColor: "#fff5f4",
    color: "#e85f33",
    duration: 1800,
    value: data.announcementCount,
    data: data.announcementCountData
  };

  const transactionCountBaseInfo: BaseInfoVO = {
    name: "成交公告数(个)",
    icon: "xxx",
    bgColor: "#eff8f4",
    color: "#26ce83",
    duration: 1800,
    value: data.transactionsCount,
    data: data.transactionsCountData
  };
  const transactionVolumeBaseInfo: BaseInfoVO = {
    name: "成交总金额(¥)",
    icon: "xxx",
    bgColor: "#effaff",
    color: "#41b6ff",
    duration: 1800,
    value: data.transactionsVolume,
    data: data.transactionsVolumeData
  };

  // 供应商
  const supplierBaseInfo: BaseInfoVO = {
    name: "供应商统计个数",
    icon: "xxx",
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
