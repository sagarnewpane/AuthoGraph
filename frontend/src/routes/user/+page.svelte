<script lang="ts">
	import type { PageData } from './$types';
	import { invalidateAll, goto } from '$app/navigation';
	import { api } from '$lib/product/api';
	import { UserRound, Bell, LockKeyhole, Check, Trash2, Upload } from 'lucide-svelte';
	export let data: PageData;
	let tab = 'profile';
	let profile = { ...data.profile };
	let notifications = { ...data.notifications };
	let busy = false;
	let error = '';
	let success = '';
	let currentPassword = '';
	let newPassword = '';
	let confirmPassword = '';
	let deletePassword = '';
	let confirmation = '';
	let deleting = false;
	let avatarInput: HTMLInputElement;
	async function save() {
		busy = true;
		error = '';
		success = '';
		try {
			if (tab === 'profile') {
				await api('/api/profile', { method: 'PATCH', body: JSON.stringify(profile) });
				await invalidateAll();
				success = 'Profile saved.';
			} else if (tab === 'notifications') {
				await api('/api/user/notification-settings', {
					method: 'PATCH',
					body: JSON.stringify(notifications)
				});
				success = 'Notification preferences saved.';
			} else {
				await api('/api/password/change', {
					method: 'POST',
					body: JSON.stringify({
						current_password: currentPassword,
						new_password: newPassword,
						confirm_password: confirmPassword
					})
				});
				await fetch('/logout', { method: 'POST' });
				await goto('/login?reset=1');
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unable to save changes.';
		} finally {
			busy = false;
		}
	}
	async function uploadAvatar() {
		const file = avatarInput.files?.[0];
		if (!file) return;
		busy = true;
		error = '';
		try {
			const body = new FormData();
			body.append('avatar', file);
			await api('/api/profile/avatar', { method: 'POST', body });
			await invalidateAll();
			profile.avatar_url = `/api/profile/avatar?v=${Date.now()}`;
			success = 'Profile photo updated.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unable to upload photo.';
		} finally {
			busy = false;
		}
	}
	async function deleteAccount() {
		busy = true;
		error = '';
		try {
			await api('/api/delete-account', {
				method: 'DELETE',
				body: JSON.stringify({ password: deletePassword, confirmation })
			});
			await fetch('/logout', { method: 'POST' });
			await goto('/login');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unable to delete account.';
		} finally {
			busy = false;
		}
	}
	const notificationLabels: Record<string, { title: string; description: string }> = {
		notify_on_access_request: {
			title: 'Access requests',
			description: 'When someone asks for permission to view an image.'
		},
		notify_on_download: {
			title: 'Image downloads',
			description: 'When a verified recipient downloads a shared copy.'
		},
		notify_on_successful_access: {
			title: 'Verified views',
			description: 'When a recipient successfully verifies and opens a link.'
		},
		notify_on_failed_access: {
			title: 'Failed access attempts',
			description: 'When a link password or verification code is incorrect.'
		}
	};
</script>

<svelte:head><title>Settings · AuthoGraph</title></svelte:head>
<div class="page-heading">
	<div>
		<h1>Settings</h1>
		<p>The details that make this workspace yours.</p>
	</div>
</div>
<div class="settings-layout">
	<nav aria-label="Settings">
		{#each [{ id: 'profile', title: 'Your profile', icon: UserRound }, { id: 'notifications', title: 'Notifications', icon: Bell }, { id: 'security', title: 'Account security', icon: LockKeyhole }] as item}<button
				class:active={tab === item.id}
				on:click={() => {
					tab = item.id;
					error = '';
					success = '';
				}}><svelte:component this={item.icon} aria-hidden="true" size={17} />{item.title}</button
			>{/each}
	</nav>
	<section class="stack">
		{#if error}<div class="error" role="alert">{error}</div>{/if}{#if success}<div
				class="success"
				role="status"
			>
				{success}
			</div>{/if}
		<form class="panel panel-pad form-stack" on:submit|preventDefault={save}>
			{#if tab === 'profile'}<h2>Your profile</h2>
				<div class="profile-avatar">
					<div>
						{#if profile.avatar_url}<img
								src={profile.avatar_url}
								alt="Your profile"
							/>{:else}{profile.username.slice(0, 2).toUpperCase()}{/if}
					</div>
					<input
						bind:this={avatarInput}
						type="file"
						accept="image/png,image/jpeg,image/webp"
						class="sr-only"
						aria-label="Profile photo"
						on:change={uploadAvatar}
					/><button type="button" class="btn" disabled={busy} on:click={() => avatarInput.click()}
						><Upload aria-hidden="true" size={15} />Change photo</button
					><span class="muted small">Up to 5 MB</span>
				</div>
				<div class="field-row">
					<div class="field">
						<label for="first">First name</label><input
							id="first"
							bind:value={profile.first_name}
							autocomplete="given-name"
						/>
					</div>
					<div class="field">
						<label for="last">Last name</label><input
							id="last"
							bind:value={profile.last_name}
							autocomplete="family-name"
						/>
					</div>
				</div>
				<div class="field">
					<label for="username">Username</label><input
						id="username"
						bind:value={profile.username}
						required
						autocomplete="username"
						maxlength="150"
					/>
				</div>
				<div class="field">
					<label for="email">Email address</label><input
						id="email"
						type="email"
						bind:value={profile.email}
						required
						autocomplete="email"
					/>
				</div>{:else if tab === 'notifications'}<h2>Email notifications</h2>
				<p class="small muted">
					Choose what you hear about. Verification emails are always sent when requested.
				</p>
				{#each Object.entries(notificationLabels) as [key, item]}<label class="check notification"
						><input type="checkbox" bind:checked={notifications[key]} /><span
							><strong>{item.title}</strong><small>{item.description}</small></span
						></label
					>{/each}{:else}<h2>Change password</h2>
				<p class="muted small">Updating your password signs out existing sessions.</p>
				<div class="field">
					<label for="current">Current password</label><input
						id="current"
						type="password"
						bind:value={currentPassword}
						required
						autocomplete="current-password"
					/>
				</div>
				<div class="field">
					<label for="new">New password</label><input
						id="new"
						type="password"
						bind:value={newPassword}
						required
						minlength="8"
						autocomplete="new-password"
					/><small>At least 8 characters with uppercase, lowercase, a number, and a symbol.</small>
				</div>
				<div class="field">
					<label for="confirm">Confirm new password</label><input
						id="confirm"
						type="password"
						bind:value={confirmPassword}
						required
						autocomplete="new-password"
					/>
				</div>{/if}
			<div class="row" style="padding-top:8px">
				<button class="btn primary" disabled={busy}
					><Check aria-hidden="true" size={16} />{busy ? 'Saving…' : 'Save changes'}</button
				>
			</div>
		</form>
		{#if tab === 'security'}<section class="panel panel-pad form-stack">
				<h2>Delete account</h2>
				<p class="small muted">
					This permanently deletes your account, uploaded images, share links, and associated access
					records.
				</p>
				{#if deleting}<form class="form-stack" on:submit|preventDefault={deleteAccount}>
						<div class="field">
							<label for="delete-password">Current password</label><input
								id="delete-password"
								type="password"
								autocomplete="current-password"
								bind:value={deletePassword}
								required
							/>
						</div>
						<div class="field">
							<label for="delete-confirm">Type “delete my account” to confirm</label><input
								id="delete-confirm"
								bind:value={confirmation}
								required
							/>
						</div>
						<div class="row wrap">
							<button class="btn danger" disabled={busy || confirmation !== 'delete my account'}
								>Delete permanently</button
							><button type="button" class="btn" on:click={() => (deleting = false)}>Cancel</button>
						</div>
					</form>{:else}<button class="btn danger" on:click={() => (deleting = true)}
						><Trash2 aria-hidden="true" size={15} />Delete account</button
					>{/if}
			</section>{/if}
	</section>
</div>

<style>
	.settings-layout {
		display: grid;
		grid-template-columns: 200px minmax(0, 660px);
		gap: 32px;
	}
	.settings-layout nav {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.settings-layout nav button {
		display: flex;
		align-items: center;
		gap: 10px;
		border: 0;
		background: none;
		border-radius: 8px;
		padding: 14px 16px;
		text-align: left;
		min-height: 46px;
		color: var(--muted-ink);
		font-size: 12px;
		font-weight: 600;
	}
	.settings-layout nav button.active {
		background: var(--studio-soft);
		color: var(--studio);
	}
	.profile-avatar {
		display: flex;
		align-items: center;
		gap: 16px;
		flex-wrap: wrap;
		margin: 8px 0 16px;
	}
	.profile-avatar > div {
		width: 64px;
		height: 64px;
		display: grid;
		place-items: center;
		background: var(--studio-soft);
		color: var(--studio);
		font-size: 19px;
		font-weight: 700;
		border-radius: 50%;
		overflow: hidden;
	}
	.profile-avatar img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.profile-avatar > span {
		font-size: 12px;
	}
	.notification {
		padding: 16px 0;
		border-bottom: 1px solid var(--line);
	}
	@media (max-width: 1000px) {
		.settings-layout {
			grid-template-columns: 1fr;
		}
		.settings-layout nav {
			flex-direction: row;
			flex-wrap: wrap;
			gap: 5px;
		}
		.settings-layout nav button {
			padding: 12px;
			font-size: 12px;
		}
	}
</style>
