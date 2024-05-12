import { BiddingDistrictStats } from "@/api/bidding";
import { PieChartData } from "@/views/home/utils/types";

export type DistrictLevelPieChartData = {
  name: string;
  value: number;
  count: number;
};

export const transformToPieChartData = (
  data: BiddingDistrictStats
): Array<DistrictLevelPieChartData> => {
  const result: Array<DistrictLevelPieChartData> = [];
  result.push({
    name: '省级',
    value: data.provincialAmount,
    count: data.provincialCount
  });
  result.push({
    name: '市级',
    value: data.municipalAmount,
    count: data.municipalCount,
  });
  result.push({
    name: '区级',
    value: data.districtAmount,
    count: data.districtCount
  });
  return result;
};
