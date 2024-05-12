import { PieChartData } from "@/views/home/utils/types";
import { ProcurementMethodItem, ProcurementMethodYearData } from "@/api/procurement";

export type ProcurementMethodChartData = {
  year: number;
  count: PieChartData[];
  transaction: PieChartData[];
};

/**
 * 将数据转换为饼图的格式
 * */
export const transformToPieChartData = (data: Array<ProcurementMethodYearData>): Array<ProcurementMethodChartData> => {
  data.sort((a: ProcurementMethodYearData, b: ProcurementMethodYearData) => {
    return a.year - b.year;
  });

  // 统计总数
  const totalResult: Map<string, ProcurementMethodItem> = new Map();
  // 每一年的数据
  data.forEach(item => {
    // 每一个采购方式的数据
    item.value.forEach(valueItem => {
      if (!totalResult.get(valueItem.name)) {
        totalResult.set(valueItem.name, valueItem);
      } else {
        const cached = totalResult.get(valueItem.name);
        cached.amount += valueItem.amount;
        cached.count += valueItem.count;
      }
    });
  });
  data.push({
    year: 10000,
    value: Array.from(totalResult.values())
  });
  // 将每一项数据转换为对应的PieChartData
  return data.map((item: ProcurementMethodYearData) => {
    const counts: Array<PieChartData> = [];
    const transactions: Array<PieChartData> = [];
    item.value.forEach(x => {
      counts.push({ name: x.name, value: x.count });
      transactions.push({ name: x.name, value: x.amount });
    });
    return {
      year: item.year,
      count: counts,
      transaction: transactions
    };
  });
}
