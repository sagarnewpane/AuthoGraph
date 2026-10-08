import { redirect, json } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';
import { backendURL, authCookie, proxyHeaders } from '$lib/server/backend';
import type { User } from '$lib/types';
const protectedPaths = [
	'/images',
	'/user',
	'/watermark',
	'/access',
	'/metadata',
	'/ai-protection',
	'/logs',
	'/activity',
	'/requests',
	'/links'
];
export const handle: Handle = async ({ event, resolve }) => {
	event.locals.user = null;
	event.locals.isAuthenticated = false;
	const access = event.cookies.get('access_token');
	const refresh = event.cookies.get('refresh_token');
	// Recipient routes use a separate verified session. API proxies let Django validate owner JWTs.
	const needsUser =
		!event.url.pathname.startsWith('/api/') && !event.url.pathname.startsWith('/share/');
	if (needsUser && (access || refresh)) {
		try {
			let response = access
				? await fetch(`${backendURL()}/verify/`, {
						headers: { ...proxyHeaders(event), Authorization: `Bearer ${access}` },
						signal: AbortSignal.timeout(8000)
					})
				: null;
			if ((!response || response.status === 401) && refresh) {
				const renewed = await fetch(`${backendURL()}/token/refresh/`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json', ...proxyHeaders(event) },
					body: JSON.stringify({ refresh }),
					signal: AbortSignal.timeout(8000)
				});
				if (renewed.ok) {
					const tokens = await renewed.json();
					event.cookies.set(
						'access_token',
						tokens.access,
						authCookie(event.url.protocol === 'https:')
					);
					response = await fetch(`${backendURL()}/verify/`, {
						headers: { ...proxyHeaders(event), Authorization: `Bearer ${tokens.access}` },
						signal: AbortSignal.timeout(8000)
					});
				} else if (renewed.status === 401) {
					event.cookies.delete('access_token', { path: '/' });
					event.cookies.delete('refresh_token', { path: '/' });
				}
			}
			if (response?.ok) {
				event.locals.user = (await response.json()) as User;
				event.locals.isAuthenticated = true;
			}
		} catch {
			/* Keep cookies on temporary backend outages. */
		}
	}
	const isProtected = protectedPaths.some(
		(p) => event.url.pathname === p || event.url.pathname.startsWith(`${p}/`)
	);
	if (isProtected && !event.locals.isAuthenticated) redirect(303, '/login');
	if (
		event.url.pathname.startsWith('/api/') &&
		!['GET', 'HEAD', 'OPTIONS'].includes(event.request.method)
	) {
		if (event.request.headers.get('origin') !== event.url.origin)
			return json({ error: 'Invalid request origin.' }, { status: 403 });
	}
	const response = await resolve(event);
	response.headers.set('X-Content-Type-Options', 'nosniff');
	response.headers.set('Referrer-Policy', 'same-origin');
	response.headers.set('X-Frame-Options', 'DENY');
	if (access || event.url.pathname.startsWith('/share/'))
		response.headers.set('Cache-Control', 'private, no-store');
	return response;
};
