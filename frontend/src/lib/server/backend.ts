import { createHmac } from 'node:crypto';
import { env } from '$env/dynamic/private';
import { error } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';
import { errorMessage } from '$lib/product/api';
export const backendURL = () => (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export async function backend(
	event: Pick<RequestEvent, 'cookies' | 'fetch'> & Partial<Pick<RequestEvent, 'getClientAddress'>>,
	path: string,
	options: RequestInit = {}
) {
	const headers = new Headers(options.headers);
	for (const [key, value] of Object.entries(proxyHeaders(event))) headers.set(key, value);
	const token = event.cookies.get('access_token');
	if (token) headers.set('Authorization', `Bearer ${token}`);
	try {
		return await event.fetch(`${backendURL()}${path}`, {
			...options,
			headers,
			signal: AbortSignal.timeout(45000)
		});
	} catch {
		error(503, 'The image service is unavailable. Please try again.');
	}
}
export async function loadBackend<T>(
	event: Pick<RequestEvent, 'cookies' | 'fetch'>,
	path: string
): Promise<T> {
	const response = await backend(event, path);
	const data = await response
		.json()
		.catch(() => ({ error: 'The server returned an unexpected response.' }));
	if (!response.ok) error(response.status, errorMessage(data));
	return data as T;
}
export function authCookie(secure: boolean, maxAge = 3600) {
	return { path: '/', httpOnly: true, secure, sameSite: 'lax' as const, maxAge };
}

export function proxyHeaders(
	event: Partial<Pick<RequestEvent, 'getClientAddress'>>
): Record<string, string> {
	if (!env.INTERNAL_PROXY_SECRET || !event.getClientAddress) return {};
	const ip = event.getClientAddress();
	const timestamp = String(Math.floor(Date.now() / 1000));
	return {
		'X-Authograph-IP': ip,
		'X-Authograph-Time': timestamp,
		'X-Authograph-Signature': createHmac('sha256', env.INTERNAL_PROXY_SECRET)
			.update(`${timestamp}:${ip}`)
			.digest('hex')
	};
}
