import type { PageServerLoad } from './$types';
import { loadBackend } from '$lib/server/backend';
export const load: PageServerLoad = async (event) => {
	const [profile, notifications] = await Promise.all([
		loadBackend<{
			username: string;
			first_name: string;
			last_name: string;
			email: string;
			avatar_url: string | null;
			social_links: Record<string, string>;
		}>(event, '/api/profile/'),
		loadBackend<Record<string, boolean>>(event, '/api/user/notification-settings/')
	]);
	return { profile, notifications };
};
