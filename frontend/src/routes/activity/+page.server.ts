import type { PageServerLoad } from './$types';
import { loadBackend } from '$lib/server/backend';
import type { PageResult, AccessEntry } from '$lib/types';
export const load: PageServerLoad = async (event) => ({
	records: await loadBackend<PageResult<AccessEntry>>(
		event,
		`/access-logs/?${event.url.searchParams}`
	)
});
