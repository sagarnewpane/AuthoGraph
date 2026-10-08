<script lang="ts">
	import Brand from './Brand.svelte';
	import { ArrowUpRight } from 'lucide-svelte';
</script>

<header>
	<Brand />
	<nav aria-label="Main">
		<a href="/#how-it-works">How it works</a><a href="/learn/access">Protection guide</a><a
			href="/verify-image">Check signature</a
		>
	</nav>
	<div class="row">
		<a href="/login" class="sign-in">Sign in</a><a href="/register" class="btn primary"
			>Get started <ArrowUpRight size={16} aria-hidden="true" /></a
		>
	</div>
</header>

<style>
	header {
		height: 88px;
		padding: 0 6%;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 24px;
		max-width: 1600px;
		margin: 0 auto;
	}
	nav {
		display: flex;
		gap: 32px;
		font-size: 12px;
		color: var(--muted-ink);
		font-weight: 600;
	}
	nav a,
	.sign-in {
		min-height: 44px;
		display: flex;
		align-items: center;
	}
	.sign-in {
		font-size: 12px;
		font-weight: 700;
		padding: 0 12px;
	}
	nav a:hover,
	.sign-in:hover {
		color: var(--studio);
	}
	@media (max-width: 800px) {
		header {
			height: 76px;
			padding: 0 20px;
			gap: 8px;
		}
		nav {
			display: none;
		}
		.sign-in {
			display: none;
		}
		header :global(.btn) {
			font-size: 12px;
			padding: 10px 12px;
		}
	}
</style>
