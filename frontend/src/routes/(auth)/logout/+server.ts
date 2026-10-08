import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
export const POST: RequestHandler = ({ cookies, request, url }) => {
	if (request.headers.get('origin') !== url.origin)
		return json({ error: 'Invalid origin' }, { status: 403 });
	cookies.delete('access_token', { path: '/' });
	cookies.delete('refresh_token', { path: '/' });
	return json({ success: true });
};
