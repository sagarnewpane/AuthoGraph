import type { PageServerLoad } from './$types';
import { loadBackend } from '$lib/server/backend';
import type { PageResult, ImageItem } from '$lib/types';
export const load: PageServerLoad = async (event) => {
	event.depends('data:images');
	return {
		images: await loadBackend<PageResult<ImageItem>>(event, `/images/?${event.url.searchParams}`)
	};
};
