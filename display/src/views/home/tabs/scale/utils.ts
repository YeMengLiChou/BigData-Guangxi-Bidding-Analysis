import { ScaleData } from "@/api/base";
import { LineChartData } from "@/views/home/utils/types";

/**
 * 将数据转换为方便图标展示的数据
 * */
export const transformToChartData = (
  param: ScaleData
): Map<number, LineChartData[]> => {
  const result: Map<number, LineChartData[]> = new Map();
  param.data
    .sort((a, b) => {
      return a.year - b.year;
    })
    .forEach(item => {
      const year = item.year;
      const daysChartData: LineChartData = {
        xAxisData: [],
        yAxisData: []
      };
      const monthsChartData: LineChartData = {
        xAxisData: [],
        yAxisData: []
      };
      const quarterChartData: LineChartData = {
        xAxisData: [],
        yAxisData: []
      };
      item.days
        .sort((a, b) => {
          if (a.month == b.month) return a.day - b.day;
          else return a.month - b.month;
        })
        .forEach(dayItem => {
          daysChartData.xAxisData.push(
            `0${dayItem.month}`.slice(-2) + '月' + `0${dayItem.day}`.slice(-2) + '日'
          );
          daysChartData.yAxisData.push(dayItem.value);
        });

      item.months
        .sort((a, b) => {
          return a.idx - b.idx;
        })
        .forEach(monthItem => {
          monthsChartData.xAxisData.push(`${monthItem.idx}月`);
          monthsChartData.yAxisData.push(monthItem.value);
        });

      item.quarters
        .sort((a, b) => {
          return a.idx - b.idx;
        })
        .forEach(quarterItem => {
          quarterChartData.xAxisData.push(`第${quarterItem.idx}季度`);
          quarterChartData.yAxisData.push(quarterItem.value);
        });

      result.set(year - 2022, [daysChartData, monthsChartData, quarterChartData]);
    });
  return result;
};


const number_to_unit = [
  [1, ''],
  [1e4, '万'],
  [1e6, '百万'],
  [1e7, '千万'],
  [1e8, '亿']
]
export const formatAmount = (param: number, fixed: number = 4): string => {
  const len = number_to_unit.length;
  for (let i = len - 1; i >= 0; i --) {
    if (number_to_unit[i][0] as number <= param) {
      const res = (param / (number_to_unit[i][0] as number)).toFixed(fixed);
      return `${res}${number_to_unit[i][1]}元`;
    }
  }
  return String(param);
};

