export function errorMessage(data: unknown): string {
	if (typeof data === 'string') return data;
	if (Array.isArray(data)) return data.map(errorMessage).join(' ');
	if (data && typeof data === 'object') {
		const obj = data as Record<string, unknown>;
		if (obj.error || obj.detail) return errorMessage(obj.error || obj.detail);
		return Object.entries(obj)
			.map(([key, value]) => `${key.replaceAll('_', ' ')}: ${errorMessage(value)}`)
			.join(' ');
	}
	return 'Something went wrong. Please try again.';
}
export async function api<T = Record<string, unknown>>(
	path: string,
	options: RequestInit = {}
): Promise<T> {
	const headers = new Headers(options.headers);
	if (options.body && !(options.body instanceof FormData))
		headers.set('Content-Type', 'application/json');
	const response = await fetch(path, { ...options, headers });
	if (response.status === 204) return {} as T;
	const data = await response
		.json()
		.catch(() => ({ error: 'The server could not complete this request.' }));
	if (!response.ok) throw new Error(errorMessage(data));
	return data as T;
}
export function bytes(value: number | string) {
	if (typeof value === 'string') return value;
	if (value < 1024) return `${value} B`;
	if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`;
	if (value < 1024 ** 3) return `${(value / 1024 ** 2).toFixed(1)} MB`;
	return `${(value / 1024 ** 3).toFixed(1)} GB`;
}
export function date(value: string) {
	const d = new Date(value);
	return Number.isNaN(d.getTime())
		? value
		: d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}
