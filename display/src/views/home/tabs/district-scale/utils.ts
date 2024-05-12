import { TransactionVolumeDistrictYear } from "@/api/transaction";


export type TransactionGeoChartItem = {
  name: string,
  value: number,
};

export const transformToGeoChartData = (param: Array<TransactionVolumeDistrictYear>): Array<Array<TransactionGeoChartItem>> => {
  if (!param || param.length == 0) {
    return [];
  }
  param.sort((a, b) => {
    return a.year - b.year;
  });

  return param.map(outerItem => {
    return outerItem.data.map(item => {
      return {
        name: item.districtName,
        value: item.volume,
      };
    });
  });
}
