import { ApiResult } from "@/api/types";
import { http } from "@/utils/http";

export type BaseInfo = {
  announcementCount: number;
  transactionsVolume: number;
  transactionsCount: number;
  latestTimestamp: number;
  supplierCount: number;
  announcementCountData: number[];
  transactionsCountData: number[];
  transactionsVolumeData: number[];
};

/*
 * 获取基本数据
 * */
export const fetchBaseInfo = () => {
  return http.get<ApiResult<BaseInfo>, any>("/api/base");
};

export type ScaleItem = {
  idx: number;
  value: number;
};

export type ScaleDayItem = {
  day: number;
  month: number;
  value: number;
};

export type ScaleYearItem = {
  year: number;
  days: ScaleDayItem[];
  months: ScaleItem[];
  quarters: ScaleItem[];
};

export type ScaleData = {
  data: ScaleYearItem[];
};


/**
 * 获取采购规模
 * */
export const fetchScaleData = () => {
  return http.get<ApiResult<ScaleData>, any>("/api/base/scale");
};
