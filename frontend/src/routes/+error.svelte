<script lang="ts">
	import { page } from '$app/stores';
	import { ArrowLeft, RefreshCw } from 'lucide-svelte';
</script>

<svelte:head><title>{$page.status} · AuthoGraph</title></svelte:head>
<section class="error-page">
	<span class="eyebrow">AUTHOGRAPH / {$page.status}</span>
	<h1>{$page.status === 404 ? 'This page isn’t here.' : 'We couldn’t open this page.'}</h1>
	<p>{$page.error?.message || 'Please try again in a moment.'}</p>
	<div class="row wrap">
		<a href="/" class="btn"><ArrowLeft aria-hidden="true" size={16} />Back to workspace</a><button
			class="btn primary"
			on:click={() => location.reload()}><RefreshCw aria-hidden="true" size={16} />Try again</button
		>
	</div>
</section>

<style>
	.error-page {
		padding: 80px 24px;
		max-width: 680px;
		margin: auto;
	}
	.error-page h1 {
		margin: 24px 0 16px;
	}
	.error-page p {
		color: var(--muted-ink);
		margin-bottom: 28px;
	}
</style>
