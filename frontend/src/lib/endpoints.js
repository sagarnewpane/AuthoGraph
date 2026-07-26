import { env } from '$env/dynamic/public';

const BACKEND_URL = (env.PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');

/** @param {string | number} id */
const imageEndpoint = (id) => `${BACKEND_URL}/image/${id}/`;

export const API_ENDPOINTS = {
	LOGIN: `${BACKEND_URL}/token/`,
	REFRESH: `${BACKEND_URL}/token/refresh/`,
	REGISTER: `${BACKEND_URL}/api/register/`,
	VERIFY: `${BACKEND_URL}/verify/`,
	PASSWORD_RESET_CONFIRM: `${BACKEND_URL}/api/password-reset-confirm/`,
	UPLOAD: `${BACKEND_URL}/upload/`,
	IMAGES: `${BACKEND_URL}/images/`,
	IMAGE: imageEndpoint
};
