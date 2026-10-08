<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import AppShell from '$lib/product/AppShell.svelte';
	import PublicNav from '$lib/product/PublicNav.svelte';
	import Brand from '$lib/product/Brand.svelte';
	import type { LayoutData } from './$types';
	export let data: LayoutData;
	$: isAuthPage = ['/login', '/register', '/forget-password'].some((p) =>
		$page.url.pathname.startsWith(p)
	);
	$: isShare = $page.url.pathname.startsWith('/share/');
	$: workspace = data.isAuthenticated && !isAuthPage && !isShare;
</script>

<svelte:head
	><title>AuthoGraph — Your work, shared on your terms</title><meta
		name="description"
		content="A private workspace for your images. Add watermarks, control access, and see how your work is shared."
	/></svelte:head
>
<a href="#main" class="skip">Skip to content</a>
{#if workspace && data.user}<AppShell user={data.user}><slot /></AppShell
	>{:else if isAuthPage || isShare}<slot />{:else}<PublicNav />
	<main id="main"><slot /></main>
	<footer class="public-footer">
		<Brand />
		<p>Your work, shared on your terms.</p>
		<div>
			<a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/learn/access">Help</a><a
				href="/verify-image">Check signature</a
			>
		</div>
		<small>© {new Date().getFullYear()} AuthoGraph</small>
	</footer>{/if}

<style>
	.public-footer {
		display: flex;
		align-items: center;
		gap: 24px;
		flex-wrap: wrap;
		border-top: 1px solid var(--line);
		padding: 32px 6%;
		background: white;
	}
	.public-footer p {
		color: var(--muted-ink);
		font-size: 12px;
		flex: 1;
	}
	.public-footer div {
		display: flex;
		gap: 24px;
		font-size: 12px;
	}
	.public-footer small {
		color: var(--muted-ink);
		font-size: 12px;
		width: 100%;
	}
	@media (max-width: 600px) {
		.public-footer {
			padding: 28px 20px;
		}
		.public-footer p {
			flex-basis: 100%;
		}
	}
</style>
