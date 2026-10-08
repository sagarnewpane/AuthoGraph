<script lang="ts">
	import { onMount } from 'svelte';
	import { Copy, Link2, Plus, Check, Ban, RotateCcw, Trash2, ArrowUpRight } from 'lucide-svelte';
	import { api, date } from './api';
	import type { AccessRule, ImageItem } from '$lib/types';
	import Empty from './Empty.svelte';
	import ShareDeliverySettings from './ShareDeliverySettings.svelte';
	export let imageId: number;
	export let imageName = '';
	export let unsavedProtection = false;
	export let security: Record<string, boolean> = {};
	let rules: AccessRule[] = [];
	let loading = true;
	let error = '';
	let success = '';
	let creating = false;
	let busy = false;
	let name = '';
	let emails = '';
	let password = '';
	let download = false;
	let filename = '';
	let showWatermark = true;
	let downloadWithoutWatermark = false;
	let includeMetadata = true;
	let downloadMetadataMode: 'inherit' | 'include' | 'strip' = 'inherit';
	let editing = 0;
	let editFilename = '';
	let editWatermark = true;
	let editDownload = false;
	let editWithoutWatermark = false;
	let editMetadata = true;
	let editDownloadMetadata: 'inherit' | 'include' | 'strip' = 'inherit';
	let maxViews = 0;
	let expires = '';
	let copied = 0;
	async function load() {
		try {
			const [links, image] = await Promise.all([
				api<{ rules: AccessRule[] }>(`/api/images/${imageId}/access`),
				api<ImageItem>(`/api/images/${imageId}`)
			]);
			rules = links.rules;
			security = image.security || {};
			imageName = image.image_name;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not load links.';
		} finally {
			loading = false;
		}
	}
	onMount(load);
	const protectionLabels: Record<string, string> = {
		watermark: 'Visible watermark',
		hidden_watermark: 'Hidden message',
		metadata: 'Metadata',
		ai_protection: 'AI processing'
	};
	function protectionChanged(rule: AccessRule) {
		return Object.keys(protectionLabels).some(
			(key) =>
				!['watermark', 'metadata'].includes(key) &&
				!!rule.protection_features[key] !== !!security[key]
		);
	}
	function edit(rule: AccessRule) {
		editing = rule.id;
		editFilename = rule.shared_filename || imageName;
		editWatermark = rule.show_watermark;
		editDownload = rule.allow_download;
		editWithoutWatermark = rule.download_without_watermark;
		editMetadata = !!rule.protection_features.metadata;
		editDownloadMetadata = rule.download_metadata_mode;
	}
	async function saveDelivery(rule: AccessRule) {
		busy = true;
		error = '';
		try {
			await api(`/api/images/${imageId}/access/${rule.id}`, {
				method: 'PATCH',
				body: JSON.stringify({
					shared_filename: editFilename,
					show_watermark: editWatermark,
					allow_download: editDownload,
					download_without_watermark: editWithoutWatermark,
					download_metadata_mode: editDownloadMetadata,
					protection_features: { metadata: editMetadata }
				})
			});
			await load();
			editing = 0;
			success = 'Sharing settings saved. Recipients must verify again.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not save sharing settings.';
		} finally {
			busy = false;
		}
	}
	async function updateProtection(rule: AccessRule) {
		busy = true;
		error = '';
		try {
			const features = Object.fromEntries(
				Object.keys(protectionLabels)
					.filter((key) => key !== 'metadata')
					.map((key) => [key, !!security[key]])
			);
			await api(`/api/images/${imageId}/access/${rule.id}`, {
				method: 'PATCH',
				body: JSON.stringify({ protection_features: features })
			});
			await load();
			success = 'Link protection updated. Recipients must verify again to see the updated copy.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not update link protection.';
		} finally {
			busy = false;
		}
	}
	async function create() {
		if (unsavedProtection) {
			error = 'Save your protection changes before creating a link.';
			return;
		}
		busy = true;
		error = '';
		success = '';
		try {
			await api(`/api/images/${imageId}/access`, {
				method: 'POST',
				body: JSON.stringify({
					access_name: name,
					allowed_emails: emails
						.split(/[,\n]/)
						.map((e) => e.trim())
						.filter(Boolean),
					requires_password: !!password,
					password: password || null,
					allow_download: download,
					shared_filename: filename,
					show_watermark: showWatermark,
					download_without_watermark: downloadWithoutWatermark,
					download_metadata_mode: downloadMetadataMode,
					protection_features: { metadata: includeMetadata },
					max_views: Number(maxViews),
					expires_at: expires ? new Date(expires).toISOString() : null
				})
			});
			creating = false;
			name = '';
			emails = '';
			password = '';
			success = 'Share link created. Copy it and send it to your recipient.';
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not create this link.';
		} finally {
			busy = false;
		}
	}
	async function revoke(rule: AccessRule) {
		busy = true;
		error = '';
		try {
			await api(`/api/images/${imageId}/access/${rule.id}`, {
				method: 'PATCH',
				body: JSON.stringify({ revoked: !rule.revoked })
			});
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not update link.';
		} finally {
			busy = false;
		}
	}
	async function copy(rule: AccessRule) {
		try {
			await navigator.clipboard.writeText(`${location.origin}/share/${rule.token}`);
			copied = rule.id;
			success = 'Link copied.';
		} catch {
			error = 'Clipboard access is unavailable. Open the link and copy its address.';
		}
	}
	function expired(rule: AccessRule) {
		return (
			rule.revoked ||
			(rule.expires_at && new Date(rule.expires_at) < new Date()) ||
			(rule.max_views > 0 && rule.current_views >= rule.max_views)
		);
	}
</script>

<div class="stack">
	<div class="row between wrap">
		<div>
			<h2>Share with intention</h2>
			<p class="small muted" style="margin-top:6px">
				Every recipient verifies their email before viewing.
			</p>
		</div>
		<button
			class="btn primary"
			disabled={unsavedProtection || busy}
			on:click={() => {
				filename = imageName;
				includeMetadata = !!security.metadata;
				creating = !creating;
			}}><Plus aria-hidden="true" size={16} />Create a link</button
		>
	</div>
	{#if error}<div class="error" role="alert">{error}</div>{/if}{#if success}<div
			class="success"
			role="status"
		>
			{success}
		</div>{/if}{#if creating}<form
			class="panel panel-pad form-stack"
			on:submit|preventDefault={create}
		>
			<div class="field">
				<label for="link-name">Link name (only you see this)</label><input
					id="link-name"
					bind:value={name}
					placeholder="Client review, campaign preview…"
					required
					maxlength="255"
				/>
			</div>
			<div class="field">
				<label for="recipients">Allowed recipients</label><textarea
					id="recipients"
					bind:value={emails}
					placeholder="client@example.com, producer@example.com"></textarea><small
					>Separate emails with commas. Leave empty to allow anyone with the link to verify their
					email.</small
				>
			</div>
			<div class="field-row">
				<div class="field">
					<label for="link-password">Link password <span class="muted">(optional)</span></label
					><input
						id="link-password"
						type="password"
						bind:value={password}
						autocomplete="new-password"
					/>
				</div>
				<div class="field">
					<label for="expiry">Expires at <span class="muted">(optional)</span></label><input
						id="expiry"
						type="datetime-local"
						bind:value={expires}
					/>
				</div>
			</div>
			<div class="field">
				<label for="max-views">Maximum verified views</label><input
					id="max-views"
					type="number"
					min="0"
					max="1000000"
					bind:value={maxViews}
				/><small>Zero means unlimited. Expiry and revocation apply to every image request.</small>
			</div>
			<ShareDeliverySettings
				bind:filename
				bind:showWatermark
				bind:allowDownload={download}
				bind:downloadWithoutWatermark
				bind:includeMetadata
				bind:downloadMetadataMode
				watermarkAvailable={!!security.watermark}
			/>
			<div class="notice">
				This link uses your currently enabled image protection. A visible image can still be
				captured in a screenshot.
			</div>
			<div class="row">
				<button class="btn primary" disabled={busy || unsavedProtection}
					>{busy ? 'Creating…' : 'Create share link'}</button
				><button type="button" class="btn" disabled={busy} on:click={() => (creating = false)}
					>Cancel</button
				>
			</div>
		</form>{/if}{#if loading}<p role="status" class="muted small">
			Loading share links…
		</p>{:else if !rules.length}<div class="panel">
			<Empty
				title="No links out in the world yet"
				description="Create a link when this image is ready to be seen. You choose the recipients and permissions."
				action=""
			/>
		</div>{:else}{#each rules as rule}<article class="rule">
				<div class="rule-icon"><Link2 aria-hidden="true" size={20} /></div>
				<div class="grow">
					<div class="row wrap">
						<h3>{rule.access_name || 'Untitled link'}</h3>
						<span class:green={!expired(rule)} class="badge"
							>{rule.revoked ? 'Revoked' : expired(rule) ? 'Unavailable' : 'Active'}</span
						>
					</div>
					<p class="small muted">
						{rule.allowed_emails.length
							? rule.allowed_emails.join(', ')
							: 'Anyone with the link · Email verification required'}
					</p>
					<div class="rule-details">
						<span>{rule.current_views}{rule.max_views ? ` / ${rule.max_views}` : ''} views</span
						><span>{rule.expires_at ? `Expires ${date(rule.expires_at)}` : 'No expiry'}</span><span
							>{rule.allow_download
								? rule.download_without_watermark
									? 'Download without visible watermark'
									: 'Download same as preview'
								: 'Viewing only'}</span
						>
					</div>
					<div class="rule-details">
						<span
							>Visible watermark: {rule.show_watermark && security.watermark ? 'On' : 'Off'}</span
						>
						<span>Filename: {rule.shared_filename || imageName}</span>
						<span
							>Preview metadata: {rule.protection_features.metadata ? 'Included' : 'Stripped'}</span
						>
						{#if rule.allow_download}<span
								>Download metadata: {rule.download_metadata_mode === 'inherit'
									? 'Same as preview'
									: rule.download_metadata_mode === 'include'
										? 'Included'
										: 'Stripped'}</span
							>{/if}
						{#each Object.entries(protectionLabels).filter(([key]) => !['watermark', 'metadata'].includes(key) && rule.protection_features[key]) as [key, label]}<span
								>{label}</span
							>{/each}
					</div>
					{#if editing === rule.id}<form
							class="form-stack"
							style="margin-top:20px"
							on:submit|preventDefault={() => saveDelivery(rule)}
						>
							<ShareDeliverySettings
								prefix={`link-${rule.id}`}
								bind:filename={editFilename}
								bind:showWatermark={editWatermark}
								bind:allowDownload={editDownload}
								bind:downloadWithoutWatermark={editWithoutWatermark}
								bind:includeMetadata={editMetadata}
								bind:downloadMetadataMode={editDownloadMetadata}
								watermarkAvailable={!!security.watermark}
							/>
							<div class="row">
								<button class="btn primary" disabled={busy}>Save sharing settings</button>
								<button class="btn" type="button" on:click={() => (editing = 0)}>Cancel</button>
							</div>
						</form>{:else}<button
							type="button"
							class="btn"
							style="margin-top:12px"
							disabled={busy}
							on:click={() => edit(rule)}>Edit sharing settings</button
						>{/if}
					{#if protectionChanged(rule)}<button
							type="button"
							class="btn"
							disabled={busy}
							on:click={() => updateProtection(rule)}
							style="margin-top:12px">Apply saved image protection to this link</button
						>{/if}
				</div>
				<div class="row wrap">
					<button
						class="icon-btn"
						aria-label={`Copy ${rule.access_name} link`}
						on:click={() => copy(rule)}
						>{#if copied === rule.id}<Check aria-hidden="true" size={16} />{:else}<Copy
								aria-hidden="true"
								size={16}
							/>{/if}</button
					><a
						class="icon-btn"
						href={`/share/${rule.token}`}
						target="_blank"
						rel="noreferrer"
						aria-label="Open share link"><ArrowUpRight aria-hidden="true" size={16} /></a
					><button
						class="icon-btn"
						disabled={busy}
						aria-label={rule.revoked ? 'Restore link' : 'Revoke link'}
						on:click={() => revoke(rule)}
						>{#if rule.revoked}<RotateCcw aria-hidden="true" size={16} />{:else}<Ban
								aria-hidden="true"
								size={16}
							/>{/if}</button
					>
				</div>
			</article>{/each}{/if}
</div>

<style>
	.rule {
		display: flex;
		align-items: center;
		gap: 16px;
		padding: 22px;
		border: 1px solid var(--line);
		border-radius: 12px;
		background: white;
	}
	.rule-icon {
		height: 44px;
		width: 44px;
		display: grid;
		place-items: center;
		background: var(--studio-soft);
		color: var(--studio);
		border-radius: 10px;
	}
	.rule p {
		font-size: 12px;
		margin-top: 8px;
		overflow-wrap: anywhere;
	}
	.rule-details {
		display: flex;
		gap: 14px;
		flex-wrap: wrap;
		font-size: 12px;
		color: var(--muted-ink);
		margin-top: 10px;
	}
	.rule h3 {
		font-size: 13px;
	}
	@media (max-width: 1050px) {
		.rule {
			flex-wrap: wrap;
		}
		.rule > .grow {
			flex-basis: 70%;
		}
	}
	@media (max-width: 480px) {
		.rule {
			padding: 18px;
		}
		.rule-icon {
			display: none;
		}
	}
</style>
