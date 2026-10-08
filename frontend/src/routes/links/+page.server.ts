import type { PageServerLoad } from './$types';
import { loadBackend } from '$lib/server/backend';
import type { PageResult, AccessRule } from '$lib/types';
export const load: PageServerLoad = async (event) => ({
	records: await loadBackend<PageResult<AccessRule>>(event, `/links/?${event.url.searchParams}`)
});
