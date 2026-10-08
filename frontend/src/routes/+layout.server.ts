import type { LayoutServerLoad } from './$types';
export const load: LayoutServerLoad = ({ locals, depends }) => {
	depends('app:auth');
	return { user: locals.user, isAuthenticated: locals.isAuthenticated };
};
