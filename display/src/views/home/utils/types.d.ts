export type BaseInfoVO = {
  name: string;
  icon: any;
  color: string;
  duration: number;
  bgColor: string;
  value: number;
  data: Array<number>;
};

/**
 * 折线图的数据
 * */
export type LineChartData = {
  xAxisData: string[];
  yAxisData: number[];
};

/**
 * 饼图的数据类型
 * */
export type PieChartData = {
  name: string,
  value: number,
}
