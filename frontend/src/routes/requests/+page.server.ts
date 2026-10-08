import type { PageServerLoad } from './$types';
import { loadBackend } from '$lib/server/backend';
import type { PageResult, AccessRequest } from '$lib/types';
export const load: PageServerLoad = async (event) => ({
	records: await loadBackend<PageResult<AccessRequest>>(
		event,
		`/access-requests/?${event.url.searchParams}`
	)
});
