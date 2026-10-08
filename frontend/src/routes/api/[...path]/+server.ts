import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { backend, authCookie } from '$lib/server/backend';
const mappings: [RegExp, string][] = [
	[/^verify-signature$/, '/api/verify-signature/'],
	[/^images$/, '/images/'],
	[/^upload$/, '/upload/'],
	[/^workspace$/, '/workspace/'],
	[/^links$/, '/links/'],
	[/^images\/(\d+)$/, '/image/$1/'],
	[/^images\/(\d+)\/(decrypted|preview|ai-protection)$/, '/images/$1/$2/'],
	[/^images\/(\d+)\/access(?:\/(\d+))?$/, '/images/$1/access/$2/'],
	[/^image\/(\d+)\/watermark-settings$/, '/api/image/$1/watermark-settings/'],
	[/^hidden-message\/(\d+)$/, '/api/image/$1/invisible-watermark/'],
	[/^metadata\/(\d+)$/, '/api/image/$1/metadata/'],
	[/^metadata\/(\d+)\/custom$/, '/api/image/$1/metadata/custom/'],
	[/^profile$/, '/api/profile/'],
	[/^profile\/avatar$/, '/api/profile/avatar/'],
	[/^password\/change$/, '/api/password/change/'],
	[/^user\/notification-settings$/, '/api/user/notification-settings/'],
	[/^delete-account$/, '/api/delete-account/'],
	[/^access-logs(?:\/(\d+))?$/, '/access-logs/$1/'],
	[/^access-requests(?:\/(\d+))?$/, '/access-requests/$1/'],
	[/^access\/([A-Za-z0-9_-]+)\/(initiate|verify|request|image)$/, '/access/$1/$2/'],
	[/^access\/([A-Za-z0-9_-]+)\/download$/, '/api/access/$1/download-protected/']
];
const handler: RequestHandler = async (event) => {
	const path = event.params.path.replace(/\/$/, '');
	const match = mappings.find(([pattern]) => pattern.test(path));
	if (!match) return json({ error: 'Not found.' }, { status: 404 });
	const publicRoute = path.startsWith('access/') || path === 'verify-signature';
	if (!publicRoute && !event.cookies.get('access_token'))
		return json({ error: 'Please sign in again.' }, { status: 401 });
	const target = path.replace(match[0], match[1]).replaceAll('//', '/') + event.url.search;
	const headers = new Headers();
	const contentType = event.request.headers.get('content-type');
	if (contentType) headers.set('Content-Type', contentType);
	const token = path.startsWith('access/') ? path.split('/')[1] : '';
	if (token) {
		const grant = event.cookies.get(`viewer_${token}`);
		if (grant) headers.set('X-Viewer-Token', grant);
	}
	const body = ['GET', 'HEAD'].includes(event.request.method)
		? undefined
		: await event.request.arrayBuffer();
	// Do not attach an owner JWT to public viewer routes.
	const context = publicRoute
		? {
				fetch: event.fetch,
				getClientAddress: event.getClientAddress,
				cookies: { get: () => undefined } as unknown as typeof event.cookies
			}
		: event;
	const response = await backend(context, target, { method: event.request.method, headers, body });
	if (publicRoute && path.endsWith('/verify') && response.ok) {
		const data = await response.json();
		event.cookies.set(`viewer_${token}`, data.viewer_token, {
			...authCookie(event.url.protocol === 'https:', data.expires_in),
			path: `/api/access/${token}`
		});
		delete data.viewer_token;
		return json(data, { headers: { 'Cache-Control': 'no-store' } });
	}
	const resultHeaders = new Headers({
		'Cache-Control': 'private, no-store',
		'X-Content-Type-Options': 'nosniff'
	});
	for (const key of ['content-type', 'content-disposition', 'retry-after']) {
		const value = response.headers.get(key);
		if (value) resultHeaders.set(key, value);
	}
	return new Response(response.body, { status: response.status, headers: resultHeaders });
};
export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const PUT = handler;
export const DELETE = handler;
