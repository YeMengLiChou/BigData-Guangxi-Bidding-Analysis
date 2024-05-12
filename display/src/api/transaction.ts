import { http } from "@/utils/http";
import { ApiResult } from "@/api/types";


export type TransactionVolumeDistrictItem = {
  districtCode: number,
  districtName: string,
  volume: number
};

export type TransactionVolumeDistrictYear = {
  year: number,
  data: TransactionVolumeDistrictItem[]
};


/**
 * 所有市级地区的成交量
 * */
export const fetchTransactionVolumeWithAllDistrict = (): Promise<ApiResult<Array<TransactionVolumeDistrictYear>>> => {
  return http.get<ApiResult<Array<TransactionVolumeDistrictYear>>, any>("/api/transaction/all")
};

/**
 * 获取指定 [code] 下所有地区的成交量
 * */
export const fetchTransactionVolumeByDistrictCode = (code: number) => {
  return http.get<ApiResult<Array<TransactionVolumeDistrictYear>>, any>(`/api/transaction?districtCode=${code}`)
};




export type TransactionGrowthItem = {
  timestamp: number,
  value: number
};

export type DistrictTransactionGrowthItem = {
  districtName: string,
  districtCode: number,
  data: TransactionGrowthItem[],
};

/***
 获取所有市级地区的成交变化情况（月份）
 */
export const fetchAllCitiesTransactionGrowth = (): Promise<ApiResult<Array<DistrictTransactionGrowthItem>>> => {
  return http.get<ApiResult<Array<DistrictTransactionGrowthItem>>, any>("/api/transaction/growth");
};
