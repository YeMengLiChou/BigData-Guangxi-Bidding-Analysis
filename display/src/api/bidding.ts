import { http } from "@/utils/http";
import { ApiResult, BiddingAnnouncement, BiddingRequest, Page } from "./types";



export const getBiddingAnnouncements = (params: BiddingRequest) => {
  return http.get<ApiResult<Page<BiddingAnnouncement>>, BiddingRequest>("/api/bidding", { params });
};

export type BiddingDistrictStats= {
  provincialCount: number,
  provincialAmount: number,
  municipalCount: number,
  municipalAmount: number,
  districtCount: number,
  districtAmount: number,
  id: number
};


export const fetchBiddingDistrictStats = () => {
  return http.get<ApiResult<BiddingDistrictStats>, any>("/api/bidding/level");
};


export type BiddingCountItem = {
  year: number,
  winCount: number,
  loseCount: number,
  terminateCount: number
};


/**
 * 获取各个年份的公告个数数据
 * */
export const fetchBiddingCount = () => {
  return http.get<ApiResult<Array<BiddingCountItem>>, any>("/api/bidding/count");
}
