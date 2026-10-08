import type { PageServerLoad } from './$types';
import { loadBackend } from '$lib/server/backend';
import type { ImageItem, PageResult, Workspace, AccessEntry, AccessRequest } from '$lib/types';
export const load: PageServerLoad = async (event) => {
	if (!event.locals.isAuthenticated) return {};
	const [images, workspace, activity, requests] = await Promise.all([
		loadBackend<PageResult<ImageItem>>(event, '/images/?page_size=4'),
		loadBackend<Workspace>(event, '/workspace/'),
		loadBackend<PageResult<AccessEntry>>(event, '/access-logs/?page_size=5'),
		loadBackend<PageResult<AccessRequest>>(event, '/access-requests/?page_size=3')
	]);
	return { images, workspace, activity, requests };
};
