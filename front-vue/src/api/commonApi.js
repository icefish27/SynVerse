import { request, get, post, put, del } from "@/utils/request.js";

/**
 * 通用文件上传地址 （例子）
 */
export const uploadFile = (data) =>
  request({
    name: "上传文件",
    url: `/api/index/upload`,
    method: "post",
    data,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

/**
 * 请求自己（例子）
 */
export function indexTest(params = {}) {
  return request({
    url: "/",
    method: "get",
    data: params,
  });
}
