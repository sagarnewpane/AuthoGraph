import type { PageServerLoad } from './$types';
import { loadBackend } from '$lib/server/backend';
import type { ImageItem } from '$lib/types';
export const load: PageServerLoad = async (event) => ({
	image: await loadBackend<ImageItem>(event, `/image/${event.params.id}/`)
});
