import type { PageServerLoad } from './$types';
export const load: PageServerLoad = ({ params }) => ({ token: params.token });
