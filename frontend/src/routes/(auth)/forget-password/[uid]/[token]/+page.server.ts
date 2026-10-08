import type { Actions } from './$types';
import { authAction } from '$lib/server/auth-actions';
export const actions: Actions = { default: (event) => authAction(event, 'reset') };
