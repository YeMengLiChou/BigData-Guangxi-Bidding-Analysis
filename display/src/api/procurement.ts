import { http } from "@/utils/http";
import { ApiResult } from "@/api/types";

/**
 * 单个item：
 * @param name 采购方法的名称
 * @param value 对应的值
 * */
export type ProcurementMethodItem = {
  name: string,
  count: number,
  amount: number
};

/**
 * 年数据
 * */
export type ProcurementMethodYearData = {
  year: number,
  value: ProcurementMethodItem[]
};

/**
 * 包含统计个数和成交量的实体
 * */

export const fetchProcurementMethodData = () => {
  return http.get<ApiResult<Array<ProcurementMethodYearData>>, any>("/api/method/stats")
}


