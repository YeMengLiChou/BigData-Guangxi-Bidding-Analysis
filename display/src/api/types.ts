export type ApiResult<T> = {
  code: number,
  msg: String,
  data: T|null
}


export type Page<T> = {
  total: number,
  data: Array<T>,
  size: number
}



export type PageRequest = {
  pageSize: number;
  pageNo: number;
};

export type BiddingRequest = {
  districtCode: number;
  year: number;
  month: number;
  day: number;
  quarter: number;
  pageNo: number;
  pageSize: number;
};

export type stringOrNull = string | null;

/**
 * @description BiddingAnnouncement实体类型
 */
export type BiddingAnnouncement = {
  resultSourceArticleId: stringOrNull;
  purchaseSourceArticleId: stringOrNull;
  title: stringOrNull;
  purchaseTitle: stringOrNull;
  scrapeTimestamp: number;
  projectName: stringOrNull;
  projectCode: stringOrNull;
  districtCode: number;
  districtName: stringOrNull;
  author: stringOrNull;
  catalog: stringOrNull;
  procurementMethod: stringOrNull;
  bidOpeningTime: number;
  isWinBid: boolean;
  resultArticleId: string;
  resultPublishDates: string;
  purchaseArticleId: string;
  purchasePublishDates: string;
  totalBudget: number;
  totalAmount: number;
  bidItems: string;
  tenderDuration: number;
  purchaser: string;
  purchasingAgency: string;
  reviewExperts: string;
  purchaseRepresentatives: string;
  isTermination: boolean;
  terminationReason: stringOrNull;
  id: number;
};


export type BidItem = {
  name: stringOrNull,
  index: number,
  is_win: boolean,
  budget: number,
  amount: number,
  is_percent: number,
  supplier: stringOrNull,
  supplier_address: stringOrNull,
  reason: stringOrNull
}

