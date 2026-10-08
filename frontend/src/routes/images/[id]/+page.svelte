<script lang="ts">
	import type { PageData } from './$types';
	import { page } from '$app/stores';
	import { goto, invalidateAll } from '$app/navigation';
	import { onMount } from 'svelte';
	import {
		ArrowLeft,
		Download,
		ShieldCheck,
		Check,
		Link2,
		Image as ImageIcon,
		Settings2,
		FileText,
		Trash2,
		RefreshCw,
		Eye,
		LockKeyhole
	} from 'lucide-svelte';
	import { api, bytes, date } from '$lib/product/api';
	import ShareRules from '$lib/product/ShareRules.svelte';
	import WatermarkPreview from '$lib/product/WatermarkPreview.svelte';
	export let data: PageData;
	let tab = 'protection';
	$: tab = $page.url.searchParams.get('tab') || 'protection';
	let watermark = {
		enabled: false,
		settings: {
			text: '© My studio',
			fontSize: 32,
			opacity: 45,
			rotation: -30,
			color: '#ffffff',
			pattern: 'tiled',
			spacing: 80,
			horizontalOffset: 0,
			verticalOffset: 0,
			font: 'Arial'
		}
	};
	let hidden = { enabled: false, text: '' };
	let metadata: Record<string, unknown> = {};
	let ai = { enabled: false, available: false };
	let consent = false;
	let busy = false;
	let loading = true;
	let error = '';
	let success = '';
	let protectedPreview = false;
	let version = 0;
	let savedWatermark = '';
	let savedHidden = '';
	let observedWatermark = '';
	$: watermarkSignature = JSON.stringify(watermark);
	$: watermarkDirty = !!savedWatermark && watermarkSignature !== savedWatermark;
	$: protectionDirty = watermarkDirty || (!!savedHidden && JSON.stringify(hidden) !== savedHidden);
	$: if (!loading && watermarkSignature !== observedWatermark) {
		observedWatermark = watermarkSignature;
		protectedPreview = true;
	}
	let deleteConfirm = false;
	let metaName = '';
	let metaValue = '';
	let imageName = '';
	$: imageName = data.image.image_name;
	async function load() {
		try {
			[watermark, hidden, ai] = await Promise.all([
				api<typeof watermark>(`/api/image/${data.image.id}/watermark-settings`),
				api<typeof hidden>(`/api/hidden-message/${data.image.id}`),
				api<typeof ai>(`/api/images/${data.image.id}/ai-protection`)
			]);
			savedWatermark = JSON.stringify(watermark);
			savedHidden = JSON.stringify(hidden);
			observedWatermark = savedWatermark;
			protectedPreview = watermark.enabled || hidden.enabled || ai.enabled;
			const result = await api<{ metadata: Record<string, unknown> }>(
				`/api/metadata/${data.image.id}`
			);
			metadata = result.metadata;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not load protection settings.';
		} finally {
			loading = false;
		}
	}
	onMount(load);
	async function saveProtection() {
		busy = true;
		error = '';
		success = '';
		try {
			await api(`/api/image/${data.image.id}/watermark-settings`, {
				method: 'POST',
				body: JSON.stringify(watermark)
			});
			await api(`/api/hidden-message/${data.image.id}`, {
				method: 'POST',
				body: JSON.stringify(hidden)
			});
			savedWatermark = JSON.stringify(watermark);
			savedHidden = JSON.stringify(hidden);
			await invalidateAll();
			version++;
			protectedPreview = true;
			success = 'Protection saved. The preview shows your protected copy.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not save protection.';
		} finally {
			busy = false;
		}
	}
	async function saveMetadata() {
		busy = true;
		error = '';
		try {
			const result = await api<{ metadata: Record<string, unknown> }>(
				`/api/metadata/${data.image.id}/custom`,
				{ method: 'POST', body: JSON.stringify({ tag_name: metaName, value: metaValue }) }
			);
			metadata = result.metadata;
			metaName = '';
			metaValue = '';
			success = 'Ownership details saved.';
			version++;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not save metadata.';
		} finally {
			busy = false;
		}
	}
	async function removeMeta(field: string) {
		error = '';
		try {
			await api(`/api/metadata/${data.image.id}?field=${encodeURIComponent(field)}`, {
				method: 'DELETE'
			});
			await load();
			version++;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Could not remove field.';
		}
	}
	async function processAI() {
		busy = true;
		error = '';
		try {
			await api(`/api/images/${data.image.id}/ai-protection`, {
				method: ai.enabled ? 'DELETE' : 'POST',
				body: ai.enabled ? undefined : JSON.stringify({ consent })
			});
			await load();
			await invalidateAll();
			version++;
			success = ai.enabled
				? 'Processed copy saved. AI resistance is experimental.'
				: 'AI processing disabled.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Processing failed.';
		} finally {
			busy = false;
		}
	}
	async function rename() {
		busy = true;
		error = '';
		try {
			await api(`/api/images/${data.image.id}`, {
				method: 'PATCH',
				body: JSON.stringify({ image_name: imageName })
			});
			await invalidateAll();
			success = 'Image renamed.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Rename failed.';
		} finally {
			busy = false;
		}
	}
	async function remove() {
		busy = true;
		error = '';
		try {
			await api(`/api/images/${data.image.id}`, { method: 'DELETE' });
			await goto('/images');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Delete failed.';
			busy = false;
		}
	}
	function valueText(v: unknown): string {
		return v && typeof v === 'object' && 'value' in v
			? String((v as { value: unknown }).value)
			: typeof v === 'object'
				? JSON.stringify(v)
				: String(v);
	}
</script>

<svelte:head><title>{data.image.image_name} · AuthoGraph</title></svelte:head><a
	href="/images"
	class="text-link"
	style="margin-bottom:12px"><ArrowLeft aria-hidden="true" size={15} />Back to library</a
>
<div class="page-heading">
	<div class="grow">
		<h1 style="overflow-wrap:anywhere">{data.image.image_name}</h1>
		<p>
			{data.image.file_type.toUpperCase()} · {bytes(data.image.file_size)} · Added {date(
				data.image.created_at
			)}
		</p>
	</div>
	<a href={`/api/images/${data.image.id}/decrypted?download=1`} class="btn" download
		><Download aria-hidden="true" size={16} />Original</a
	>
</div>
<div class="image-workspace">
	<aside class="image-preview">
		<div class="preview-head">
			<span class="eyebrow">{protectedPreview ? 'PROTECTED COPY' : 'YOUR ORIGINAL'}</span><span
				class="badge purple"><LockKeyhole aria-hidden="true" size={11} />Private</span
			>
		</div>
		<div class="preview-canvas">
			{#if protectedPreview && !loading}<WatermarkPreview
					imageId={data.image.id}
					refreshKey={version}
					{watermark}
					fallback={`/api/images/${data.image.id}/preview?v=${version}`}
					alt={data.image.image_name}
					on:previewerror={(event) => (error = event.detail)}
				/>{:else}<img
					src={data.image.image_url}
					alt={data.image.image_name}
					on:error={() => {
						error =
							'The preview could not be rendered. Check the protection settings and try again.';
					}}
				/>{/if}
		</div>
		{#if watermarkDirty}<p class="small muted" role="status" style="padding:0 20px">
				Unsaved watermark preview. Save protection to apply it.
			</p>{/if}
		{#if !watermark.enabled && !loading}<p class="small muted" style="padding:0 20px">
				Visible watermark is off. Hidden messages do not display text on the image.
			</p>{/if}
		<div class="preview-footer">
			<div class="preview-toggle">
				<button class:active={!protectedPreview} on:click={() => (protectedPreview = false)}
					>Original</button
				><button
					class:active={protectedPreview}
					on:click={() => {
						version++;
						protectedPreview = true;
					}}>Protected</button
				>
			</div>
			<a
				class="icon-btn"
				href={`/api/images/${data.image.id}/preview?download=1`}
				download
				aria-label="Download protected image"><Download aria-hidden="true" size={16} /></a
			>
		</div>
		<p class="small muted" style="padding:0 20px 20px;font-size:12px">
			Originals are kept privately. Share links deliver a separate copy with your chosen protection.
		</p>
	</aside>
	<section class="editor">
		<nav class="tabs" aria-label="Image tools">
			{#each [{ id: 'protection', label: 'Protection', icon: ShieldCheck }, { id: 'sharing', label: 'Sharing', icon: Link2 }, { id: 'metadata', label: 'Metadata', icon: FileText }, { id: 'settings', label: 'Details', icon: Settings2 }] as item}<a
					class="tab"
					class:active={tab === item.id}
					href={`?tab=${item.id}`}
					aria-current={tab === item.id ? 'page' : undefined}
					><svelte:component
						this={item.icon}
						aria-hidden="true"
						size={15}
						style="display:inline;vertical-align:middle;margin-right:5px"
					/>{item.label}</a
				>{/each}
		</nav>
		{#if error}<div class="error" role="alert" style="margin-bottom:20px">
				{error}
			</div>{/if}{#if success}<div class="success" role="status" style="margin-bottom:20px">
				{success}
			</div>{/if}{#if loading}<p class="muted small" role="status">
				Loading your image settings…
			</p>{:else if tab === 'sharing'}
			{#if protectionDirty}<div class="notice" style="margin-bottom:20px">
					Your watermark preview has unsaved changes. Save them before creating a share link.
					<button
						class="btn primary"
						disabled={busy}
						on:click={saveProtection}
						style="margin-top:12px">Save protection</button
					>
				</div>{/if}
			<ShareRules
				imageId={data.image.id}
				imageName={data.image.image_name}
				unsavedProtection={protectionDirty}
				security={data.image.security || {}}
			/>{:else if tab === 'metadata'}<div class="stack">
				<div>
					<h2>Ownership & metadata</h2>
					<p class="muted small" style="margin-top:8px">
						Store attribution with your image. Metadata can be removed by other software.
					</p>
				</div>
				<div class="panel panel-pad">
					<span class="eyebrow">IMAGE INFORMATION</span>
					<dl class="metadata-list">
						{#each Object.entries((metadata.basic as Record<string, unknown>) || {}) as [key, value]}<div
							>
								<dt>{key}</dt>
								<dd>{valueText(value)}</dd>
							</div>{/each}
					</dl>
					{#if !metadata.basic}<p class="muted small" style="margin-top:12px">
							This image uses legacy metadata. Its stored fields remain available below.
						</p>{/if}
				</div>
				{#if Object.keys(metadata).some((k) => !['basic', 'custom'].includes(k))}<details
						class="panel panel-pad"
					>
						<summary class="small">Original metadata</summary>
						<pre>{JSON.stringify(metadata, null, 2)}</pre>
					</details>{/if}
				<div class="panel panel-pad">
					<h3>Custom fields</h3>
					{#each Object.entries((metadata.custom as Record<string, unknown>) || {}) as [key, value]}<div
							class="metadata-entry"
						>
							<div class="grow">
								<strong>{key}</strong>
								<p>{valueText(value)}</p>
							</div>
							<button class="icon-btn" aria-label={`Remove ${key}`} on:click={() => removeMeta(key)}
								><Trash2 aria-hidden="true" size={15} /></button
							>
						</div>{/each}
					<form class="form-stack" style="margin-top:20px" on:submit|preventDefault={saveMetadata}>
						<div class="field">
							<label for="meta-name">Field name</label><input
								id="meta-name"
								bind:value={metaName}
								placeholder="Creator, copyright, usage rights…"
								required
								maxlength="100"
							/>
						</div>
						<div class="field">
							<label for="meta-value">Value</label><input
								id="meta-value"
								bind:value={metaValue}
								required
								maxlength="2000"
							/>
						</div>
						<button class="btn primary" disabled={busy}>Add field</button>
					</form>
				</div>
			</div>{:else if tab === 'settings'}<div class="stack">
				<form class="panel panel-pad form-stack" on:submit|preventDefault={rename}>
					<h2>Image details</h2>
					<div class="field">
						<label for="image-name">Image name</label><input
							id="image-name"
							bind:value={imageName}
							maxlength="255"
							required
						/>
					</div>
					<button class="btn primary" disabled={busy}>Save name</button>
				</form>
				<div class="panel panel-pad form-stack">
					<h2>AI resistance <span class="badge">Experimental</span></h2>
					<p class="small muted">
						Image perturbation may affect some AI models. It does not guarantee protection against
						training or editing.
					</p>
					{#if ai.available}<label class="check"
							><input type="checkbox" bind:checked={consent} /><span
								>I agree to send this image to the workspace's configured external processing
								service.</span
							></label
						><button class="btn" disabled={busy || (!ai.enabled && !consent)} on:click={processAI}
							>{busy
								? 'Processing…'
								: ai.enabled
									? 'Disable AI processing'
									: 'Process image'}</button
						>{:else}<div class="notice">
							External AI processing is not configured for this workspace.
						</div>{/if}
				</div>
				<div class="panel panel-pad form-stack">
					<h2>Delete image</h2>
					<p class="small muted">
						Permanently remove this image and its share links. This cannot be undone.
					</p>
					{#if deleteConfirm}<div class="error">
							Delete “{data.image.image_name}” and revoke all of its share links?
						</div>
						<div class="row">
							<button class="btn danger" disabled={busy} on:click={remove}
								>Delete permanently</button
							><button class="btn" disabled={busy} on:click={() => (deleteConfirm = false)}
								>Cancel</button
							>
						</div>{:else}<button class="btn danger" on:click={() => (deleteConfirm = true)}
							><Trash2 aria-hidden="true" size={15} />Delete image</button
						>{/if}
				</div>
			</div>{:else}<form class="stack" on:submit|preventDefault={saveProtection}>
				<div>
					<h2>Leave your signature</h2>
					<p class="muted small" style="margin-top:8px">
						Apply protection to the copies you share.
					</p>
				</div>
				<div class="panel panel-pad form-stack">
					<label class="check"
						><input type="checkbox" bind:checked={watermark.enabled} /><span
							><strong>Visible watermark</strong><small
								>A visible reminder of who owns the work.</small
							></span
						></label
					>{#if watermark.enabled}<div class="field">
							<label for="watermark-text">Watermark text</label><input
								id="watermark-text"
								bind:value={watermark.settings.text}
								maxlength="160"
								required
							/>
						</div>
						<div class="field-row">
							<div class="field">
								<label for="pattern">Layout</label><select
									id="pattern"
									bind:value={watermark.settings.pattern}
									><option value="tiled">Repeated across image</option><option value="single"
										>Single centered mark</option
									><option value="diagonal">Diagonal</option><option value="grid">Grid</option
									><option value="corners">Corners</option></select
								>
							</div>
							<div class="field">
								<label for="wm-color">Color</label><input
									id="wm-color"
									type="color"
									bind:value={watermark.settings.color}
								/>
							</div>
						</div>
						{#each [{ key: 'opacity', label: 'Opacity', min: 5, max: 100, unit: '%' }, { key: 'fontSize', label: 'Text size', min: 12, max: 200, unit: 'px' }, { key: 'rotation', label: 'Rotation', min: -180, max: 180, unit: '°' }, { key: 'spacing', label: 'Spacing', min: 20, max: 500, unit: 'px' }] as range}<div
								class="field"
							>
								<label for={`wm-${range.key}`} class="row between"
									><span>{range.label}</span><span class="muted"
										>{watermark.settings[
											range.key as 'opacity' | 'fontSize' | 'rotation' | 'spacing'
										]}{range.unit}</span
									></label
								><input
									id={`wm-${range.key}`}
									type="range"
									min={range.min}
									max={range.max}
									bind:value={
										watermark.settings[range.key as 'opacity' | 'fontSize' | 'rotation' | 'spacing']
									}
								/>
							</div>{/each}{/if}
				</div>
				<div class="panel panel-pad form-stack">
					<label class="check"
						><input type="checkbox" bind:checked={hidden.enabled} /><span
							><strong>Hidden message</strong><small
								>Embed attribution in the image pixels. Editing or compression may remove it.</small
							></span
						></label
					>{#if hidden.enabled}<div class="field">
							<label for="hidden-text">Message</label><input
								id="hidden-text"
								bind:value={hidden.text}
								maxlength="255"
								required
								placeholder="Copyright and creator information"
							/>
						</div>{/if}
				</div>
				<div class="row between wrap">
					<span class="small muted">Preview updates as you edit. Save to apply protection.</span
					><button class="btn primary" disabled={busy}
						><Check aria-hidden="true" size={16} />{busy ? 'Saving…' : 'Save protection'}</button
					>
				</div>
			</form>{/if}
	</section>
</div>

<style>
	.image-workspace {
		display: grid;
		grid-template-columns: minmax(280px, 1fr) minmax(340px, 1.1fr);
		gap: 32px;
		align-items: start;
	}
	.image-preview {
		border: 1px solid var(--line);
		border-radius: 12px;
		background: white;
		overflow: hidden;
		position: sticky;
		top: 24px;
	}
	.preview-head,
	.preview-footer {
		padding: 18px 20px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
	}
	.preview-canvas {
		min-height: 280px;
		max-height: 580px;
		aspect-ratio: 1;
		background: #eeeff3;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 20px;
	}
	.preview-canvas img {
		width: 100%;
		height: 100%;
		object-fit: contain;
	}
	.preview-toggle {
		display: flex;
		border: 1px solid var(--line);
		padding: 3px;
		border-radius: 7px;
		background: var(--paper);
	}
	.preview-toggle button {
		font-size: 12px;
		padding: 8px 12px;
		min-height: 36px;
		border: 0;
		background: none;
		border-radius: 4px;
		color: var(--muted-ink);
	}
	.preview-toggle button.active {
		background: white;
		color: var(--studio);
		box-shadow: 0 1px 3px #20212d12;
	}
	.editor {
		min-width: 0;
	}
	.metadata-list {
		display: grid;
		gap: 12px;
		margin: 20px 0 0;
		font-size: 12px;
	}
	.metadata-list > div {
		display: flex;
		justify-content: space-between;
	}
	.metadata-list dt {
		color: var(--muted-ink);
		text-transform: capitalize;
	}
	.metadata-list dd {
		margin: 0;
	}
	.metadata-entry {
		display: flex;
		gap: 12px;
		align-items: center;
		margin-top: 18px;
		font-size: 12px;
	}
	.metadata-entry p {
		font-size: 12px;
		color: var(--muted-ink);
		overflow-wrap: anywhere;
	}
	pre {
		font-size: 12px;
		white-space: pre-wrap;
		overflow-wrap: anywhere;
		margin-top: 16px;
	}
	@media (max-width: 1200px) {
		.image-workspace {
			grid-template-columns: 1fr;
			gap: 24px;
		}
		.image-preview {
			position: static;
		}
		.preview-canvas {
			aspect-ratio: 1.8;
			min-height: 240px;
			max-height: 450px;
		}
		.editor .tabs {
			margin-top: 0;
		}
	}
	@media (max-width: 480px) {
		.preview-canvas {
			aspect-ratio: 1.2;
			padding: 12px;
		}
		.tabs .tab {
			padding: 12px 10px;
			font-size: 12px;
		}
		.tabs .tab :global(svg) {
			display: none !important;
		}
	}
</style>
