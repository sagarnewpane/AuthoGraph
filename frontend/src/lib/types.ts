export interface User {
	id: number;
	username: string;
	email: string;
	first_name?: string;
}
export interface ImageItem {
	id: number;
	image_name: string;
	image_url: string;
	file_size: number | string;
	file_type: string;
	created_at: string;
	watermark_enabled?: boolean;
	hidden_watermark_enabled?: boolean;
	access_control_enabled?: boolean;
	metadata_enabled?: boolean;
	ai_protection_enabled?: boolean;
	security?: Record<string, boolean>;
}
export interface PageResult<T> {
	count: number;
	results: T[];
	next?: string | null;
	previous?: string | null;
}
export interface Workspace {
	images: number;
	storage_bytes: number;
	storage_limit: number;
	upload_limit: number;
	active_links: number;
	views: number;
	pending_requests: number;
}
export interface AccessRule {
	id: number;
	user_image: number;
	access_name: string;
	image_name?: string;
	token: string;
	allowed_emails: string[];
	requires_password: boolean;
	allow_download: boolean;
	shared_filename: string;
	show_watermark: boolean;
	download_without_watermark: boolean;
	download_metadata_mode: 'inherit' | 'include' | 'strip';
	max_views: number;
	current_views: number;
	expires_at: string | null;
	revoked: boolean;
	created_at: string;
	protection_features: Record<string, boolean>;
}
export interface AccessEntry {
	id: number;
	email: string;
	image_name: string;
	image_id: number;
	action_type: string;
	success: boolean;
	accessed_at: string;
	ip_address?: string;
}
export interface AccessRequest {
	id: number;
	email: string;
	image_name: string;
	message: string;
	created_at: string;
	status: string;
}
