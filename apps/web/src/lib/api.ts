export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function explainApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "登录已失效，请重新登录。";
    if (error.status === 403) return "当前账号没有执行该操作的权限。";
    if (error.status === 404) return "请求的数据不存在或已不可用。";
    if (error.status === 409) return "数据版本已发生变化，请刷新后重试。";
    if (error.status >= 500) return "系统暂时无法处理请求，请稍后重试。";
    return error.message;
  }
  if (error instanceof Error && error.message) return error.message;
  return "请求失败，请检查网络或后端服务。";
}

function csrfToken(): string {
  return sessionStorage.getItem("carepath.csrf") ?? "";
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRF-Token", csrfToken());
  }

  const response = await fetch(path.startsWith("http") ? path : `/api/v1${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const payload = (await response.json()) as {
        detail?: string;
        message?: string;
      };
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Non-JSON responses use the HTTP status text.
    }
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
