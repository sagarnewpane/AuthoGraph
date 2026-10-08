<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { UploadCloud, Check, X, ImagePlus, LoaderCircle } from 'lucide-svelte';
	import { api, bytes } from './api';
	const dispatch = createEventDispatcher();
	let files: File[] = [];
	let busy = false;
	let completed = 0;
	let error = '';
	let dragging = false;
	let input: HTMLInputElement;
	function select(list: FileList | null) {
		if (!list) return;
		error = '';
		files = Array.from(list);
		if (
			files.some(
				(f) =>
					!['image/jpeg', 'image/png', 'image/webp'].includes(f.type) || f.size > 20 * 1024 * 1024
			)
		) {
			error = 'Use JPG, PNG, or WebP images, up to 20 MB each.';
			files = [];
		}
	}
	async function upload() {
		busy = true;
		error = '';
		completed = 0;
		let succeeded = 0;
		const remaining = [...files];
		try {
			for (const file of files) {
				const body = new FormData();
				body.append('image', file);
				await api('/api/upload', { method: 'POST', body });
				succeeded++;
				completed = succeeded;
				remaining.shift();
			}
			files = [];
			dispatch('complete');
		} catch (e) {
			files = remaining;
			error = e instanceof Error ? e.message : 'Upload failed.';
			if (succeeded) dispatch('partial');
		} finally {
			busy = false;
		}
	}
</script>

<div class="upload-box">
	<div class="row between" style="margin-bottom:20px">
		<div>
			<h2>Bring your work in</h2>
			<p class="muted small">Choose one image or a whole selection.</p>
		</div>
		<button
			class="icon-btn"
			disabled={busy}
			aria-label="Close upload"
			on:click={() => dispatch('close')}><X aria-hidden="true" size={18} /></button
		>
	</div>
	<input
		bind:this={input}
		type="file"
		accept="image/jpeg,image/png,image/webp"
		multiple
		class="sr-only"
		tabindex="-1"
		aria-label="Choose images"
		on:change={() => select(input.files)}
	/><button
		class:dragging
		class="dropzone"
		disabled={busy}
		on:click={() => input.click()}
		on:dragover|preventDefault={() => (dragging = true)}
		on:dragleave={() => (dragging = false)}
		on:drop|preventDefault={(e) => {
			dragging = false;
			select(e.dataTransfer?.files || null);
		}}
		><UploadCloud aria-hidden="true" size={30} strokeWidth={1.5} /><strong
			>{files.length
				? `${files.length} ${files.length === 1 ? 'image' : 'images'} selected`
				: 'Drop your images here'}</strong
		><span>or browse your files</span><small>JPG, PNG, WebP · Up to 20 MB per image</small></button
	>{#if files.length}<div class="upload-files">
			{#each files as file}<div class="row">
					<ImagePlus aria-hidden="true" size={15} /><span class="grow truncate">{file.name}</span
					><small>{bytes(file.size)}</small>
				</div>{/each}
		</div>{/if}{#if error}<div class="error" role="alert">{error}</div>{/if}{#if busy}<p
			class="small muted"
			role="status"
		>
			Uploading {completed + 1} of {files.length} images. Keep this page open.
		</p>{/if}
	<div class="row between" style="margin-top:20px">
		<span class="small muted"
			><Check aria-hidden="true" size={13} style="display:inline;vertical-align:middle" /> Visible only
			to you until shared</span
		><button class="btn primary" disabled={busy || !files.length} on:click={upload}
			>{#if busy}<LoaderCircle aria-hidden="true" size={16} />{/if}{busy
				? 'Uploading…'
				: 'Upload images'}</button
		>
	</div>
</div>

<style>
	.upload-box {
		padding: 24px;
		background: white;
		border: 1px solid var(--line);
		border-radius: 12px;
		margin-bottom: 28px;
	}
	.dropzone {
		width: 100%;
		border: 1.5px dashed #c8c4e7;
		border-radius: 10px;
		background: #fbfaff;
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 36px 20px;
		color: var(--studio);
		gap: 10px;
	}
	.dropzone:hover,
	.dropzone.dragging {
		background: var(--studio-soft);
	}
	.dropzone strong {
		font-size: 14px;
		color: var(--ink);
	}
	.dropzone span {
		font-size: 12px;
	}
	.dropzone small {
		font-size: 12px;
		color: var(--muted-ink);
		margin-top: 6px;
	}
	.upload-files {
		max-height: 180px;
		overflow: auto;
		display: grid;
		gap: 12px;
		margin: 20px 0;
		font-size: 12px;
	}
	.upload-files small {
		color: var(--muted-ink);
		font-size: 12px;
	}
	.upload-box > .error {
		margin-top: 20px;
	}
	@media (max-width: 600px) {
		.upload-box {
			padding: 18px;
		}
		.upload-box > .row:last-child {
			align-items: flex-start;
			flex-direction: column;
		}
		.upload-box > .row:last-child .btn {
			width: 100%;
		}
	}
</style>
