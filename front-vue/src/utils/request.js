import axios from "axios";
import { ElMessage } from "element-plus";
import { useUserStore } from "@/store/useUserStore";

// 默认内容类型
const CONTENT_TYPE = "application/json;charset=utf-8";
const TOKEN_HEADER = import.meta.env.VITE_REQUEST_HEADER_TOKEN || "Authorization";
const TOKEN_PREFIX = import.meta.env.VITE_REQUEST_HEADER_TOKEN_PREFIX || "";
const LOGIN_ROUTE_PATH = import.meta.env.VITE_LOGIN_ROUTE_PATH || "/auth";
const USER_STORE_PERSIST_KEY = "pinia_userstore";

let isHandlingSessionExpired = false;

// 设置 axios 默认配置
axios.defaults.headers["Content-Type"] = CONTENT_TYPE;

/**
 * 创建 axios 实例
 */
const serviceInstance = axios.create({
  // 根据环境变量配置基础 URL
  baseURL:
    import.meta.env.VITE_OPEN_PROXY === "true"
      ? import.meta.env.VITE_PROXY_URL
      : import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8080",
  timeout: 30000,
});

function getCurrentToken() {
  const userStore = useUserStore();
  return userStore.userInfo?.token || "";
}

function buildTokenHeaderValue(token) {
  if (!token) {
    return "";
  }

  if (TOKEN_HEADER.toLowerCase() === "authorization") {
    return TOKEN_PREFIX ? `${TOKEN_PREFIX}${token}` : `Bearer ${token}`;
  }

  return `${TOKEN_PREFIX}${token}`;
}

function getHeaderValue(headers, headerName) {
  if (!headers || !headerName) {
    return "";
  }

  if (typeof headers.get === "function") {
    return headers.get(headerName) || headers.get(headerName.toLowerCase()) || "";
  }

  return headers[headerName] || headers[headerName.toLowerCase()] || "";
}

function getResponseMessage(payload, fallback = "请求失败") {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  return payload.message || payload.msg || fallback;
}

function clearUserSession() {
  const userStore = useUserStore();
  userStore.clearUserInfo();

  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(USER_STORE_PERSIST_KEY);
  window.sessionStorage.removeItem(USER_STORE_PERSIST_KEY);
}

function buildLoginHash() {
  if (typeof window === "undefined") {
    return `#${LOGIN_ROUTE_PATH}`;
  }

  const currentRoute = window.location.hash.replace(/^#/, "") || "/";
  const isOnLoginPage = currentRoute.startsWith(LOGIN_ROUTE_PATH);

  if (isOnLoginPage) {
    return `#${LOGIN_ROUTE_PATH}`;
  }

  return `#${LOGIN_ROUTE_PATH}?redirect=${encodeURIComponent(currentRoute)}`;
}

function redirectToLogin() {
  if (typeof window === "undefined") {
    return;
  }

  const nextHash = buildLoginHash();
  const nextUrl = `${window.location.pathname}${window.location.search}${nextHash}`;
  window.location.replace(nextUrl);
}

function handleSessionExpired(config) {
  const token = getCurrentToken();
  const hasSession =
    Boolean(getHeaderValue(config?.headers, TOKEN_HEADER)) ||
    Boolean(getHeaderValue(config?.headers, "Authorization")) ||
    Boolean(token);

  if (!hasSession || isHandlingSessionExpired) {
    return;
  }

  isHandlingSessionExpired = true;
  clearUserSession();
  ElMessage.error("登录状态已过期，请重新登录");
  redirectToLogin();
}

/**
 * 请求拦截器
 * 用于处理请求前的配置，如添加 token、设置请求头等
 */
serviceInstance.interceptors.request.use(
  (config) => {
    const token = getCurrentToken();

    config.headers = config.headers || {};

    if (token) {
      isHandlingSessionExpired = false;
      config.headers[TOKEN_HEADER] = buildTokenHeaderValue(token);
    }

    return config;
  },
  (error) => {
    console.error("axios直接在请求拦截器,原地裂开 :", error);
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器
 * 用于处理响应数据和错误
 */
serviceInstance.interceptors.response.use(
  (response) => {
    const res = response.data;
    const shouldShowErrorMessage = response.config?.showErrorMessage !== false;

    if (
      response.config.responseType &&
      (response.config.responseType === "blob" ||
        response.config.responseType === "arraybuffer")
    ) {
      return res;
    }

    if (!res || typeof res !== "object" || !("code" in res)) {
      return res;
    }

    if (Number(res.code) === 0) {
      return res;
    }

    const businessCodePrefix = Math.floor(Number(res.code || 0) / 100);
    if (businessCodePrefix === 401) {
      handleSessionExpired(response.config);
    }

    if (shouldShowErrorMessage && businessCodePrefix !== 401) {
      ElMessage.error(getResponseMessage(res));
    }

    const error = new Error(getResponseMessage(res));
    error.code = res.code;
    error.response = res;
    return Promise.reject(error);
  },
  (error) => {
    if (error?.response?.status === 401) {
      handleSessionExpired(error.config);
    }

    const shouldShowErrorMessage = error?.config?.showErrorMessage !== false;

    if (shouldShowErrorMessage && error?.response?.status !== 401) {
      const message = getResponseMessage(
        error?.response?.data,
        error?.message || "网络异常，请稍后重试"
      );
      ElMessage.error(message);
    }

    return Promise.reject(error);
  }
);

/**
 * 封装的 HTTP 请求方法
 * @param {Object} params - 请求参数
 * @param {string} params.url - 请求 URL
 * @param {string} [params.method='get'] - 请求方法
 * @param {Object} [params.data={}] - 请求数据
 * @returns {Promise} 请求结果 Promise
 */
export const request = async (params = {}) => {
  try {
    if (!params.url) {
      throw new Error("请求 URL 未配置");
    }

    const method = params.method?.toLowerCase() || "get";
    const {
      url,
      data,
      params: queryParams,
      headers,
      responseType,
      timeout,
      showErrorMessage,
      method: _method,
      ...rest
    } = params;

    const config = {
      url,
      method,
      params: queryParams ?? (method === "get" ? data : undefined),
      data: method === "get" ? undefined : data,
      responseType,
      headers: headers || {},
      timeout,
      showErrorMessage,
      ...rest,
    };

    return await serviceInstance(config);
  } catch (error) {
    console.error("Request Exception:", error);
    return Promise.reject(error);
  }
};

/**
 * 导出常用的 HTTP 请求方法
 */
export const get = (url, params = {}, options = {}) =>
  request({ url, method: "get", params, ...options });
export const post = (url, data = {}, options = {}) =>
  request({ url, method: "post", data, ...options });
export const put = (url, data = {}, options = {}) =>
  request({ url, method: "put", data, ...options });
export const del = (url, data = {}, options = {}) =>
  request({ url, method: "delete", data, ...options });
