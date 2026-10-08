<script lang="ts">
	import { onDestroy } from 'svelte';
	import { Fingerprint, UploadCloud, ArrowRight, ShieldCheck } from 'lucide-svelte';
	import { api, bytes } from '$lib/product/api';
	type Result = {
		status: 'verified' | 'unsigned' | 'not_found' | 'invalid';
		creator: string | null;
		signature: string | null;
	};
	let input: HTMLInputElement;
	let file: File | null = null;
	let preview = '';
	let busy = false;
	let dragging = false;
	let error = '';
	let result: Result | null = null;
	const headings = {
		verified: 'Signed creator found',
		unsigned: 'Unsigned attribution found',
		not_found: 'No supported signature found',
		invalid: 'Signature could not be verified'
	};
	function select(files: FileList | null | undefined) {
		if (busy || !files?.length) return;
		error = '';
		result = null;
		if (preview) URL.revokeObjectURL(preview);
		preview = '';
		file = null;
		const selected = files[0];
		if (
			(selected.type && !['image/png', 'image/jpeg', 'image/webp'].includes(selected.type)) ||
			selected.size > 20 * 1024 * 1024
		) {
			error = 'Choose a PNG, JPG, or WebP image up to 20 MB.';
			return;
		}
		file = selected;
		preview = URL.createObjectURL(selected);
	}
	async function check() {
		if (!file || busy) return;
		busy = true;
		error = '';
		result = null;
		try {
			const body = new FormData();
			body.append('image', file);
			result = await api<Result>('/api/verify-signature', { method: 'POST', body });
		} catch (failure) {
			error = failure instanceof Error ? failure.message : 'Could not check this image.';
		} finally {
			busy = false;
		}
	}
	onDestroy(() => {
		if (preview) URL.revokeObjectURL(preview);
	});
</script>

<svelte:head
	><title>Check an image signature · AuthoGraph</title><meta
		name="description"
		content="Upload an image to read its hidden attribution and check its signed creator. No account required."
	/></svelte:head
>
<section class="signature-page">
	<div class="intro">
		<span class="eyebrow"><Fingerprint size={16} aria-hidden="true" />PUBLIC SIGNATURE CHECK</span>
		<h1>Find the signature<br />behind the image.</h1>
		<p>
			Upload an image to read its hidden attribution and check the signed creator. No account
			required.
		</p>
	</div>
	<div class="check-layout">
		<form class="panel panel-pad form-stack" aria-busy={busy} on:submit|preventDefault={check}>
			<input
				bind:this={input}
				class="sr-only"
				type="file"
				accept="image/png,image/jpeg,image/webp"
				aria-label="Choose an image to check"
				disabled={busy}
				on:change={() => select(input.files)}
			/>
			<button
				type="button"
				class="dropzone"
				class:dragging
				disabled={busy}
				on:click={() => input.click()}
				on:dragover|preventDefault={() => (dragging = true)}
				on:dragleave={() => (dragging = false)}
				on:drop|preventDefault={(event) => {
					dragging = false;
					select(event.dataTransfer?.files);
				}}
			>
				{#if preview}<img src={preview} alt="Selected file preview" />{:else}<UploadCloud
						size={36}
						strokeWidth={1.5}
						aria-hidden="true"
					/>{/if}
				<strong>{file ? 'Choose a different image' : 'Drop an image here'}</strong>
				<span>or browse your files</span><small>PNG, JPG, WebP · Up to 20 MB</small>
			</button>
			{#if file}<div class="row between file-info">
					<strong>{file.name}</strong><span class="muted small">{bytes(file.size)}</span>
				</div>{/if}
			{#if error}<div class="error" role="alert">{error}</div>{/if}
			<button class="btn primary" disabled={busy || !file}
				>{busy ? 'Checking signature…' : 'Check signature'}<ArrowRight
					size={16}
					aria-hidden="true"
				/></button
			>
			<p class="small muted">
				The image is checked for this request and is not added to anyone’s library.
			</p>
		</form>
		<div class="details">
			{#if result}<section
					class="panel panel-pad result"
					class:verified={result.status === 'verified'}
					role="status"
					aria-live="polite"
				>
					{#if result.status === 'verified'}<ShieldCheck
							size={30}
							aria-hidden="true"
						/>{:else}<Fingerprint size={30} aria-hidden="true" />{/if}
					<h2>{headings[result.status]}</h2>
					{#if result.creator}<span class="eyebrow">ATTRIBUTED CREATOR</span>
						<p class="creator">{result.creator}</p>
						<p class="small muted">
							This attribution was issued by AuthoGraph and matches the image pixels.
						</p>{/if}
					{#if result.signature !== null}<span class="eyebrow">HIDDEN MESSAGE</span>
						<blockquote>{result.signature}</blockquote>{/if}
					{#if result.status === 'unsigned'}<p class="small muted">
							This image contains a hidden message, but no verified creator record.
						</p>{:else if result.status === 'not_found'}<p class="small muted">
							This file has no readable AuthoGraph signature. Try the protected PNG downloaded from
							the share link.
						</p>{:else if result.status === 'invalid'}<p class="small muted">
							The hidden data is damaged, invalid, or belongs to a different image.
						</p>{/if}
				</section>{/if}
			<section class="panel panel-pad guidance">
				<h2>Start with the protected copy</h2>
				<p>
					Hidden signatures are embedded in the image pixels. Resizing, compression, cropping, or
					screenshots can remove them.
				</p>
				<p>
					New protected copies carry a signed creator record. Older copies may contain unsigned
					attribution, which is shown separately.
				</p>
				<a class="text-link" href="/learn/watermark"
					>How hidden signatures work <ArrowRight size={14} aria-hidden="true" /></a
				>
			</section>
		</div>
	</div>
</section>

<style>
	.signature-page {
		max-width: 1120px;
		margin: 0 auto;
		padding: 64px 6% 88px;
	}
	.intro {
		max-width: 680px;
		margin-bottom: 36px;
	}
	.intro .eyebrow {
		display: flex;
		gap: 8px;
		align-items: center;
	}
	h1 {
		font-size: clamp(32px, 5vw, 48px);
		line-height: 1.15;
		margin: 18px 0;
		letter-spacing: -1.5px;
	}
	.intro p {
		color: var(--muted-ink);
		max-width: 550px;
		line-height: 1.7;
	}
	.check-layout {
		display: grid;
		grid-template-columns: 1.1fr 1fr;
		gap: 24px;
		align-items: start;
	}
	.dropzone {
		min-height: 240px;
		width: 100%;
		border: 1px dashed var(--line);
		border-radius: 12px;
		background: var(--paper);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 24px;
		cursor: pointer;
		color: var(--studio);
	}
	.dropzone:hover,
	.dropzone.dragging {
		border-color: var(--studio);
		background: var(--studio-soft);
	}
	.dropzone span,
	.dropzone small {
		color: var(--muted-ink);
	}
	.dropzone img {
		max-width: 100%;
		max-height: 220px;
		object-fit: contain;
		border-radius: 8px;
	}
	.file-info {
		gap: 12px;
		font-size: 13px;
	}
	.file-info strong {
		overflow-wrap: anywhere;
		min-width: 0;
	}
	.file-info span {
		flex-shrink: 0;
	}
	.details {
		display: grid;
		gap: 20px;
	}
	.guidance h2,
	.result h2 {
		font-size: 18px;
		margin-bottom: 16px;
	}
	.guidance p,
	.result p {
		color: var(--muted-ink);
		line-height: 1.7;
		margin-bottom: 16px;
		font-size: 13px;
	}
	.result > :global(svg) {
		color: var(--studio);
		margin-bottom: 16px;
	}
	.result.verified {
		border-color: var(--studio);
	}
	.result .creator {
		color: var(--ink);
		font-weight: 700;
		font-size: 24px;
		margin: 12px 0;
		overflow-wrap: anywhere;
	}
	blockquote {
		margin: 14px 0;
		padding: 16px;
		border-left: 3px solid var(--studio);
		background: var(--studio-soft);
		font-size: 14px;
		white-space: pre-wrap;
		overflow-wrap: anywhere;
	}
	@media (max-width: 760px) {
		.signature-page {
			padding: 36px 20px 48px;
		}
		.check-layout {
			grid-template-columns: 1fr;
		}
	}
</style>
