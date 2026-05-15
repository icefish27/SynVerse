/**
 * 初始化性能监控系统，采集关键页面性能指标并发送到监控服务器
 * 支持：TTFB、DNS查询、TCP连接、HTTP请求、DOM解析、资源加载等核心指标
 * @returns {void}
 */
export function initPerformanceMonitoring() {
  // 使用更精准的PerformanceObserver监听性能事件
  if ("PerformanceObserver" in window) {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === "navigation") {
          handleNavigationEntry(entry);
        }
      });
    });

    // 观察导航类型的性能条目
    observer.observe({ entryTypes: ["navigation"] });

    // 页面卸载时断开观察器连接
    window.addEventListener("unload", () => observer.disconnect());
  } else {
    // 回退到传统的load事件监听方式
    window.addEventListener("load", () => {
      setTimeout(() => {
        const perfEntries = performance.getEntriesByType("navigation");
        if (perfEntries.length > 0) {
          handleNavigationEntry(perfEntries[0]);
        }
      }, 0);
    });
  }
}

/**
 * 处理导航性能条目，计算关键指标并发送
 * @param {PerformanceNavigationTiming} navEntry - 导航性能条目
 * @returns {void}
 */
function handleNavigationEntry(navEntry) {
  try {
    // 计算关键性能指标
    const metrics = calculatePerformanceMetrics(navEntry);

    // 检查是否有FP/FCP性能指标
    const paintMetrics = getPaintMetrics();
    Object.assign(metrics, paintMetrics);

    // 添加设备和网络信息
    addDeviceAndNetworkInfo(metrics);

    // 发送性能数据到监控服务器
    sendPerformanceMetrics(metrics);

    // 存储关键指标到本地缓存(可选)
    saveMetricsToLocalStorage(metrics);
  } catch (error) {
    console.error("性能指标计算失败:", error);
    // 可以添加错误上报逻辑
  }
}

/**
 * 计算性能指标
 * @param {PerformanceNavigationTiming} navEntry - 导航性能条目
 * @returns {object} 包含各种性能指标的对象
 */
function calculatePerformanceMetrics(navEntry) {
  return {
    // 首字节时间(Time To First Byte)
    ttfb: navEntry.responseStart - navEntry.startTime,
    // DNS查询时间
    dns: navEntry.domainLookupEnd - navEntry.domainLookupStart,
    // TCP连接时间
    tcp: navEntry.connectEnd - navEntry.connectStart,
    // HTTP请求响应时间
    request: navEntry.responseEnd - navEntry.requestStart,
    // 服务器处理时间
    server: navEntry.responseStart - navEntry.requestStart,
    // DOM解析时间
    dom: navEntry.domInteractive - navEntry.responseEnd,
    // 资源加载时间
    resources: navEntry.loadEventStart - navEntry.domContentLoadedEventEnd,
    // 首次内容绘制时间
    fcp: 0, // 会在getPaintMetrics中更新
    // 首次有意义绘制时间
    fmp: navEntry.domContentLoadedEventEnd - navEntry.startTime,
    // 页面完全加载时间
    load: navEntry.loadEventEnd - navEntry.startTime,
    // DOMContentLoaded事件触发时间
    domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.startTime,
    // 重定向时间
    redirect: navEntry.redirectEnd - navEntry.redirectStart,
    // SSL/TLS握手时间
    ssl: navEntry.secureConnectionStart
      ? navEntry.connectEnd - navEntry.secureConnectionStart
      : 0,
    // 缓存使用情况
    cache:
      navEntry.fetchStart === navEntry.domainLookupStart ? "no-cache" : "cache",
  };
}

/**
 * 获取绘制相关的性能指标(FP/FCP)
 * @returns {object} 包含绘制指标的对象
 */
function getPaintMetrics() {
  const paintEntries = performance.getEntriesByType("paint");
  const paintMetrics = {};

  paintEntries.forEach((entry) => {
    if (entry.name === "first-paint") {
      paintMetrics.fp = Math.round(entry.startTime);
    } else if (entry.name === "first-contentful-paint") {
      paintMetrics.fcp = Math.round(entry.startTime);
    }
  });

  return paintMetrics;
}

/**
 * 添加设备和网络信息到性能指标
 * @param {object} metrics - 性能指标对象
 * @returns {void}
 */
function addDeviceAndNetworkInfo(metrics) {
  // 添加用户代理信息
  metrics.userAgent = navigator.userAgent;

  // 添加屏幕信息
  metrics.screen = `${window.screen.width}x${window.screen.height}`;

  // 添加网络信息(如果支持)
  if ("connection" in navigator) {
    const connection = navigator.connection;
    metrics.network = {
      type: connection.type,
      effectiveType: connection.effectiveType,
      rtt: connection.rtt,
      downlink: connection.downlink,
    };
  }
}

/**
 * 发送性能指标到后端
 * @param {object} metrics - 性能指标对象
 * @returns {Promise<void>}
 */
async function sendPerformanceMetrics(metrics) {
  try {
    // 对指标进行采样，避免频繁发送
    if (!shouldSendMetrics()) return;

    // 添加时间戳和页面标识
    const payload = {
      timestamp: Date.now(),
      url: window.location.href,
      metrics,
    };

    // 这里可以替换为实际的监控接口
    console.log("发送性能指标:", payload);

    // 使用Beacon API发送数据，不阻塞页面卸载
    if (navigator.sendBeacon) {
      navigator.sendBeacon("/api/performance", JSON.stringify(payload));
    } else {
      // 回退到fetch
      await fetch("/api/performance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        keepalive: true,
      });
    }
  } catch (error) {
    console.error("发送性能指标失败:", error);
  }
}

/**
 * 存储性能指标到本地缓存(用于后续分析)
 * @param {object} metrics - 性能指标对象
 * @returns {void}
 */
function saveMetricsToLocalStorage(metrics) {
  try {
    const history = JSON.parse(
      localStorage.getItem("performanceHistory") || "[]"
    );
    history.push({
      timestamp: Date.now(),
      metrics,
    });

    // 限制历史记录数量
    if (history.length > 10) history.shift();

    localStorage.setItem("performanceHistory", JSON.stringify(history));
  } catch (error) {
    console.error("保存性能历史记录失败:", error);
  }
}

/**
 * 决定是否应该发送性能指标(采样逻辑)
 * @returns {boolean} 是否应该发送
 */
function shouldSendMetrics() {
  // 简单的采样逻辑 - 10%的概率发送
  return Math.random() < 0.1;

  // 更复杂的采样逻辑可以基于用户ID、会话ID等
  // const userId = getUserId();
  // return userId % 10 === 0; // 10%的用户会发送指标
}
