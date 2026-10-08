import { fail, redirect } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';
import { backendURL, authCookie, proxyHeaders } from './backend';
import { errorMessage } from '$lib/product/api';
export async function authAction(
	event: RequestEvent,
	mode: 'login' | 'register' | 'forgot' | 'reset'
) {
	const form = await event.request.formData();
	const field = (name: string) => String(form.get(name) || '');
	const values = { username: field('username'), email: field('email') };
	const payload =
		mode === 'login'
			? { username: values.username, password: field('password') }
			: mode === 'register'
				? { ...values, password: field('password'), password2: field('confirm_password') }
				: mode === 'forgot'
					? { email: values.email }
					: {
							uidb64: event.params.uid,
							token: event.params.token,
							new_password: field('password'),
							confirm_password: field('confirm_password')
						};
	const path = {
		login: '/token/',
		register: '/api/register/',
		forgot: '/api/password-reset/',
		reset: '/api/password-reset-confirm/'
	}[mode];
	let response: Response;
	let data: Record<string, unknown>;
	try {
		response = await fetch(`${backendURL()}${path}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', ...proxyHeaders(event) },
			body: JSON.stringify(payload),
			signal: AbortSignal.timeout(15000)
		});
		data = await response.json();
	} catch {
		return fail(503, { error: 'The server is unavailable. Please try again.', values });
	}
	if (!response.ok) return fail(response.status, { error: errorMessage(data), values });
	if (mode === 'login') {
		event.cookies.set(
			'access_token',
			String(data.access),
			authCookie(event.url.protocol === 'https:')
		);
		event.cookies.set(
			'refresh_token',
			String(data.refresh),
			authCookie(event.url.protocol === 'https:', 604800)
		);
		redirect(303, '/');
	}
	if (mode === 'register') redirect(303, '/login?registered=1');
	if (mode === 'reset') redirect(303, '/login?reset=1');
	return { message: String(data.message), values };
}
