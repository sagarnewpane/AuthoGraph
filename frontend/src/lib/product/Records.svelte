<script lang="ts">
	import { page } from '$app/stores';
	import { goto, invalidateAll } from '$app/navigation';
	import {
		ArrowUpRight,
		Copy,
		Check,
		Link2,
		ChevronLeft,
		ChevronRight,
		Search,
		ShieldCheck,
		X,
		Eye,
		Inbox,
		Ban,
		RotateCcw
	} from 'lucide-svelte';
	import { api, date } from './api';
	import Empty from './Empty.svelte';
	import type { AccessEntry, AccessRequest, AccessRule, PageResult } from '$lib/types';
	export let kind: 'activity' | 'requests' | 'links';
	export let records: PageResult<AccessEntry | AccessRequest | AccessRule>;
	let error = '';
	let success = '';
	let busy = 0;
	let copied = 0;
	let search = '';
	$: title = { activity: 'Activity', requests: 'Access requests', links: 'Share links' }[kind];
	$: description = {
		activity: 'A record of verified views, downloads, and access attempts.',
		requests: 'Decide who gets to see your work.',
		links: 'Keep track of every door you’ve opened.'
	}[kind];
	$: current = Number($page.url.searchParams.get('page') || 1);
	$: pages = Math.max(1, Math.ceil(records.count / 24));
	function query(key: string, value: string) {
		const p = new URLSearchParams($page.url.searchParams);
		p.set(key, value);
		if (key !== 'page') p.set('page', '1');
		goto(`?${p}`);
	}
	async function act(id: number, action: string) {
		busy = id;
		error = '';
		try {
			await api(`/api/access-requests/${id}`, { method: 'POST', body: JSON.stringify({ action }) });
			success =
				action === 'approve'
					? 'Access approved. The recipient can verify their email using the original link.'
					: 'Access request denied.';
			await invalidateAll();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not update request.';
		} finally {
			busy = 0;
		}
	}
	async function copy(rule: AccessRule) {
		try {
			await navigator.clipboard.writeText(`${location.origin}/share/${rule.token}`);
			copied = rule.id;
			success = 'Share link copied.';
		} catch {
			error = 'Unable to copy. Open the share link and copy its address.';
		}
	}
	async function revoke(rule: AccessRule) {
		busy = rule.id;
		try {
			await api(`/api/images/${rule.user_image}/access/${rule.id}`, {
				method: 'PATCH',
				body: JSON.stringify({ revoked: !rule.revoked })
			});
			await invalidateAll();
			success = rule.revoked ? 'Link restored. Recipients must verify again.' : 'Link revoked.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not update link.';
		} finally {
			busy = 0;
		}
	}
	function available(rule: AccessRule) {
		return (
			!rule.revoked &&
			(!rule.expires_at || new Date(rule.expires_at) > new Date()) &&
			(!rule.max_views || rule.current_views < rule.max_views)
		);
	}
</script>

<svelte:head><title>{title} · AuthoGraph</title></svelte:head>
<div class="page-heading">
	<div>
		<h1>{title}</h1>
		<p>{description}</p>
	</div>
	<span class="badge purple"
		>{records.count} {kind === 'requests' ? 'pending' : kind === 'links' ? 'links' : 'events'}</span
	>
</div>
{#if error}<div class="error" role="alert" style="margin-bottom:20px">
		{error}
	</div>{/if}{#if success}<div class="success" role="status" style="margin-bottom:20px">
		{success}
	</div>{/if}{#if kind === 'activity'}<form
		class="toolbar"
		on:submit|preventDefault={() => query('search', search)}
	>
		<div class="search">
			<Search aria-hidden="true" size={16} /><input
				aria-label="Search activity"
				placeholder="Search by email or image…"
				bind:value={search}
			/>
		</div>
		<button class="btn">Search</button><select
			class="input"
			aria-label="Filter activity"
			value={$page.url.searchParams.get('action_type') || ''}
			on:change={(e) => query('action_type', e.currentTarget.value)}
			><option value="">All events</option><option value="VIEW">Views</option><option
				value="DOWNLOAD">Downloads</option
			><option value="ATTEMPT">Attempts</option></select
		>
	</form>{/if}
<section class="panel">
	{#if !records.results.length}<Empty
			title={kind === 'requests'
				? 'No requests waiting'
				: kind === 'links'
					? 'Ready when you are'
					: 'Nothing to report yet'}
			description={kind === 'requests'
				? 'New requests from people outside your recipient list will appear here.'
				: kind === 'links'
					? 'Open an image and create a share link. Every link has its own recipients and permissions.'
					: 'Share an image to start seeing verified views and downloads here.'}
			action={kind === 'requests' ? '' : 'Go to image library'}
			href="/images"
		/>{:else if kind === 'activity'}<div class="table-wrap">
			<table>
				<thead
					><tr><th>Recipient</th><th>Image</th><th>Action</th><th>Result</th><th>Date</th></tr
					></thead
				><tbody
					>{#each records.results as record}{@const item = record as AccessEntry}<tr
							><td
								><strong>{item.email}</strong><small class="cell-note"
									>{item.ip_address || 'IP unavailable'}</small
								></td
							><td
								>{#if item.image_id}<a href={`/images/${item.image_id}`} class="record-link"
										>{item.image_name || 'Deleted image'}</a
									>{:else}{item.image_name || 'Deleted image'}{/if}</td
							><td>{item.action_type}</td><td
								><span class:green={item.success} class:red={!item.success} class="badge"
									>{item.success ? 'Verified' : 'Denied'}</span
								></td
							><td class="muted">{date(item.accessed_at)}</td></tr
						>{/each}</tbody
				>
			</table>
		</div>{:else if kind === 'requests'}{#each records.results as record}{@const item =
				record as AccessRequest}
			<article class="request-row">
				<span class="record-icon"><Inbox aria-hidden="true" size={21} /></span>
				<div class="grow">
					<h3>{item.email}</h3>
					<p class="muted small">Requests access to <strong>{item.image_name}</strong></p>
					{#if item.message}<blockquote>{item.message}</blockquote>{/if}<small class="muted"
						>{date(item.created_at)}</small
					>
				</div>
				<div class="row">
					<button class="btn" disabled={busy === item.id} on:click={() => act(item.id, 'deny')}
						><X aria-hidden="true" size={15} />Deny</button
					><button
						class="btn primary"
						disabled={busy === item.id}
						on:click={() => act(item.id, 'approve')}
						><Check aria-hidden="true" size={15} />Approve</button
					>
				</div>
			</article>{/each}{:else}<div class="table-wrap">
			<table>
				<thead
					><tr
						><th>Link & image</th><th>Recipients</th><th>Views</th><th>Status</th><th
							><span class="sr-only">Actions</span></th
						></tr
					></thead
				><tbody
					>{#each records.results as record}{@const rule = record as AccessRule}<tr
							><td
								><a class="record-link" href={`/images/${rule.user_image}?tab=sharing`}
									>{rule.access_name || 'Untitled link'}</a
								><small class="cell-note">{rule.image_name}</small></td
							><td
								>{rule.allowed_emails.length
									? `${rule.allowed_emails.length} invited`
									: 'Anyone with link'}<small class="cell-note"
									>{rule.requires_password ? 'Email + password' : 'Email verification'}</small
								></td
							><td>{rule.current_views}{rule.max_views ? ` / ${rule.max_views}` : ''}</td><td
								><span class:green={available(rule)} class="badge"
									>{rule.revoked ? 'Revoked' : available(rule) ? 'Active' : 'Unavailable'}</span
								><small class="cell-note"
									>{rule.expires_at ? `Expires ${date(rule.expires_at)}` : 'No expiry'}</small
								></td
							><td
								><div class="row">
									<button class="icon-btn" aria-label="Copy share link" on:click={() => copy(rule)}
										>{#if copied === rule.id}<Check aria-hidden="true" size={15} />{:else}<Copy
												aria-hidden="true"
												size={15}
											/>{/if}</button
									><a
										href={`/share/${rule.token}`}
										class="icon-btn"
										target="_blank"
										rel="noreferrer"
										aria-label="Open share link"><ArrowUpRight aria-hidden="true" size={15} /></a
									><button
										class="icon-btn"
										aria-label={rule.revoked ? 'Restore link' : 'Revoke link'}
										disabled={busy === rule.id}
										on:click={() => revoke(rule)}
										>{#if rule.revoked}<RotateCcw aria-hidden="true" size={15} />{:else}<Ban
												aria-hidden="true"
												size={15}
											/>{/if}</button
									>
								</div></td
							></tr
						>{/each}</tbody
				>
			</table>
		</div>{/if}
</section>
{#if pages > 1}<div class="pagination">
		<span>Page {current} of {pages}</span>
		<div class="row">
			<button
				class="icon-btn"
				aria-label="Previous page"
				disabled={current <= 1}
				on:click={() => query('page', String(current - 1))}
				><ChevronLeft aria-hidden="true" size={18} /></button
			><button
				class="icon-btn"
				aria-label="Next page"
				disabled={current >= pages}
				on:click={() => query('page', String(current + 1))}
				><ChevronRight aria-hidden="true" size={18} /></button
			>
		</div>
	</div>{/if}

<style>
	.cell-note {
		display: block;
		color: var(--muted-ink);
		font-size: 12px;
		margin-top: 6px;
	}
	.record-link {
		font-weight: 600;
		color: var(--ink);
	}
	.record-link:hover {
		color: var(--studio);
	}
	td strong {
		font-size: 12px;
		font-weight: 600;
	}
	td {
		font-size: 12px;
	}
	.request-row {
		display: flex;
		align-items: flex-start;
		gap: 20px;
		padding: 26px;
		border-bottom: 1px solid var(--line);
	}
	.request-row:last-child {
		border: 0;
	}
	.record-icon {
		height: 44px;
		width: 44px;
		display: grid;
		place-items: center;
		color: var(--studio);
		background: var(--studio-soft);
		border-radius: 10px;
	}
	.request-row h3 {
		font-size: 13px;
		overflow-wrap: anywhere;
	}
	.request-row p {
		font-size: 12px;
		margin: 8px 0;
	}
	.request-row small {
		font-size: 12px;
	}
	blockquote {
		font-size: 12px;
		color: var(--muted-ink);
		border-left: 2px solid #d0cbef;
		margin: 14px 0;
		padding: 4px 12px;
		overflow-wrap: anywhere;
	}
	@media (max-width: 1000px) {
		.request-row {
			flex-wrap: wrap;
		}
		.request-row > .grow {
			flex-basis: 70%;
		}
	}
	@media (max-width: 480px) {
		.request-row {
			padding: 20px;
		}
		.record-icon {
			display: none;
		}
	}
</style>
