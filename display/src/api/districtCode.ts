import { http } from "@/utils/http";
import { ApiResult } from "@/api/types";

export type DistrictCode = {
  code: number,
  name: string,
  fillName: string,
  shortName: string,
  parentCode: number,
  type: number
};


export const fetchCities = () => {
  return http.get<ApiResult<Array<DistrictCode>>, any>("/api/districtCode/city");
}
