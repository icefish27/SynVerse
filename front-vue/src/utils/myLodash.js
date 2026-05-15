function isObjectLike(value) {
  return typeof value === "object" && value !== null;
}

function normalizeWait(wait) {
  const normalizedValue = Number(wait);
  return Number.isFinite(normalizedValue) ? Math.max(normalizedValue, 0) : 0;
}

function cloneDeepFallback(value, cache = new WeakMap()) {
  if (!isObjectLike(value)) {
    return value;
  }

  if (cache.has(value)) {
    return cache.get(value);
  }

  if (value instanceof Date) {
    return new Date(value.getTime());
  }

  if (value instanceof RegExp) {
    return new RegExp(value.source, value.flags);
  }

  if (value instanceof Map) {
    const result = new Map();
    cache.set(value, result);

    value.forEach((mapValue, mapKey) => {
      result.set(cloneDeepFallback(mapKey, cache), cloneDeepFallback(mapValue, cache));
    });

    return result;
  }

  if (value instanceof Set) {
    const result = new Set();
    cache.set(value, result);

    value.forEach((setValue) => {
      result.add(cloneDeepFallback(setValue, cache));
    });

    return result;
  }

  if (Array.isArray(value)) {
    const result = [];
    cache.set(value, result);

    value.forEach((item, index) => {
      result[index] = cloneDeepFallback(item, cache);
    });

    return result;
  }

  const prototype = Object.getPrototypeOf(value);
  const result = Object.create(prototype || Object.prototype);
  cache.set(value, result);

  Reflect.ownKeys(value).forEach((key) => {
    result[key] = cloneDeepFallback(value[key], cache);
  });

  return result;
}

export function cloneDeep(value) {
  if (typeof structuredClone === "function") {
    try {
      return structuredClone(value);
    } catch (error) {
      // structuredClone 遇到函数等不可克隆值时，回退到手写版本
    }
  }

  return cloneDeepFallback(value);
}

export function debounce(fn, wait = 0, options = {}) {
  if (typeof fn !== "function") {
    throw new TypeError("debounce 需要传入函数");
  }

  const normalizedWait = normalizeWait(wait);

  let timerId = null;
  let lastArgs;
  let lastThis;
  let lastCallTime = 0;
  let lastInvokeTime = 0;
  let result;

  const leading = options.leading === true;
  const trailing = options.trailing !== false;
  const maxWait = Number.isFinite(options.maxWait)
    ? Math.max(Number(options.maxWait), normalizedWait)
    : null;

  function invoke(time) {
    lastInvokeTime = time;
    const args = lastArgs;
    const context = lastThis;

    lastArgs = undefined;
    lastThis = undefined;
    result = fn.apply(context, args);
    return result;
  }

  function shouldInvoke(time) {
    const timeSinceLastCall = time - lastCallTime;
    const timeSinceLastInvoke = time - lastInvokeTime;

    return (
      lastCallTime === 0 ||
      timeSinceLastCall >= normalizedWait ||
      timeSinceLastCall < 0 ||
      (maxWait !== null && timeSinceLastInvoke >= maxWait)
    );
  }

  function remainingWait(time) {
    const timeSinceLastCall = time - lastCallTime;
    const timeSinceLastInvoke = time - lastInvokeTime;
    const waitRemaining = normalizedWait - timeSinceLastCall;

    if (maxWait === null) {
      return waitRemaining;
    }

    return Math.min(waitRemaining, maxWait - timeSinceLastInvoke);
  }

  function startTimer(pendingWait) {
    timerId = globalThis.setTimeout(timerExpired, pendingWait);
  }

  function leadingEdge(time) {
    lastInvokeTime = time;
    startTimer(normalizedWait);
    return leading ? invoke(time) : result;
  }

  function trailingEdge(time) {
    timerId = null;

    if (trailing && lastArgs) {
      return invoke(time);
    }

    lastArgs = undefined;
    lastThis = undefined;
    return result;
  }

  function timerExpired() {
    const time = Date.now();

    if (shouldInvoke(time)) {
      trailingEdge(time);
      return;
    }

    startTimer(remainingWait(time));
  }

  function debounced(...args) {
    const time = Date.now();
    const isInvoking = shouldInvoke(time);

    lastArgs = args;
    lastThis = this;
    lastCallTime = time;

    if (isInvoking) {
      if (timerId === null) {
        return leadingEdge(time);
      }

      if (maxWait !== null) {
        clearTimeout(timerId);
        startTimer(normalizedWait);
        return invoke(time);
      }
    }

    if (timerId === null) {
      startTimer(normalizedWait);
    }

    return result;
  }

  debounced.cancel = () => {
    if (timerId !== null) {
      clearTimeout(timerId);
    }

    timerId = null;
    lastArgs = undefined;
    lastThis = undefined;
    lastCallTime = 0;
    lastInvokeTime = 0;
  };

  debounced.flush = () => {
    if (timerId === null) {
      return result;
    }

    return trailingEdge(Date.now());
  };

  debounced.pending = () => timerId !== null;

  return debounced;
}

export function throttle(fn, wait = 0, options = {}) {
  if (typeof fn !== "function") {
    throw new TypeError("throttle 需要传入函数");
  }

  const normalizedWait = normalizeWait(wait);
  const leading = options.leading !== false;
  const trailing = options.trailing !== false;

  return debounce(fn, normalizedWait, {
    leading,
    trailing,
    maxWait: normalizedWait,
  });
}

export default {
  cloneDeep,
  debounce,
  throttle,
};
