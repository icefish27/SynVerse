import { request, get, post, put, del } from "@/utils/request.js";

/**
 * 系统配置信息（例子）
 */
export function indexConfig(params = {}) {
  return request({
    url: "/api/index/config",
    method: "get",
    data: params,
  });
}
/**
 * 用户登录（例子）
 */
export function indexLogin(params = {}) {
  return request({
    url: "/api/index/login",
    method: "post",
    data: params,
  });
}
