import type { BiddingAnnouncement, BidItem } from "@/api/types";

export type BiddingAnnouncementVO =
  Omit<BiddingAnnouncement, "purchaseRepresentatives" | "reviewExperts" | "bidItems"> & {
  type: number;
  purchaseRepresentatives: string[],
  reviewExperts: string[],
  bidItems: Array<BidItem>
};

export const BiddingAnnouncementType = {
  success: 1, // 中标
  failure: 2, // 废标
  termination: 3 // 终止
};

/**
 * 获取 ``type`` 对应的名称
 * */
export const getAnnouncementTypeName = (type: number): string => {
  if (type == BiddingAnnouncementType.success) {
    return "成交";
  } else if (type == BiddingAnnouncementType.failure) {
    return "废标";
  } else if (type == BiddingAnnouncementType.termination) {
    return "终止";
  }
};

// 防止 :type报错，限定返回值范围
type TagType = "success" | "danger";
export const getAnnouncementTagType = (type: number): TagType => {
  if (type == BiddingAnnouncementType.success) {
    return "success";
  } else if (type == BiddingAnnouncementType.failure) {
    return "danger";
  } else if (type == BiddingAnnouncementType.termination) {
    return "danger";
  }
};

/**
 * 转化为 VO
 * */
export const mapBiddingAnnouncement = (
  announcements: Array<BiddingAnnouncement>
): Array<BiddingAnnouncementVO> => {
  return announcements.map(item => {
    const result: BiddingAnnouncementVO = {
      ...item,
      type: undefined,
      purchaseRepresentatives: JSON.parse(item.purchaseRepresentatives) as string[],
      reviewExperts: JSON.parse(item.reviewExperts) as string[],
      bidItems: JSON.parse(item.bidItems) as BidItem[],
    }
    if (item.isWinBid) {
      result.type = BiddingAnnouncementType.success;
    } else if (!item.isWinBid && item.isTermination) {
      result.type = BiddingAnnouncementType.termination;
    } else {
      result.type = BiddingAnnouncementType.failure;
    }
    return result;
  });
};

/*
* 格式化时间戳
* */
export const formatTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = `0${date.getMonth() + 1}`.slice(-2); // 月份是从0开始的，所以需要+1
  const day = `0${date.getDate()}`.slice(-2);
  const hours = `0${date.getHours()}`.slice(-2);
  const minutes = `0${date.getMinutes()}`.slice(-2);
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}


export const joinStrings = (split: string, strings: string[]): string=> {
  if (strings.length == 0) {
    return "";
  }
  if (strings.length == 1) {
    return strings[0];
  }
  let result = strings[0];
  for (let i = 1; i < strings.length; i ++) {
      result += split + strings[i];
  }
  return result;
}


export const noData = (val: string | number): string | number => {
  if (val == null) {
    return "暂无数据";
  }
  if (typeof val === 'string') {
    return val.length === 0 ? "暂无数据" : val;
  } else if (typeof val === 'number') {
    return val < 0 ? "暂无数据": val;
  }
  return val;
};

export const emptyData = (val: string | number): string | number => {
  if (val == null) {
    return "/";
  }
  if (typeof val === 'string') {
    return val.length === 0 ? "/" : val;
  } else if (typeof val === 'number') {
    return val < 0 ? "/": val;
  }
  return val;
};
