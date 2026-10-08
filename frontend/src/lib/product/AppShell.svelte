<script lang="ts">
	import { page } from '$app/stores';
	import { goto, invalidateAll } from '$app/navigation';
	import {
		LayoutDashboard,
		Images,
		Link2,
		Activity,
		Inbox,
		Settings2,
		ArrowUpRight,
		LogOut,
		Menu,
		X,
		Plus,
		ChevronRight,
		ShieldCheck,
		Fingerprint
	} from 'lucide-svelte';
	import Brand from './Brand.svelte';
	import type { User } from '$lib/types';
	export let user: User;
	let open = false;
	let signingOut = false;
	const items = [
		{ label: 'Overview', href: '/', icon: LayoutDashboard },
		{ label: 'Image library', href: '/images', icon: Images },
		{ label: 'Share links', href: '/links', icon: Link2 },
		{ label: 'Access requests', href: '/requests', icon: Inbox },
		{ label: 'Activity', href: '/activity', icon: Activity },
		{ label: 'Check signature', href: '/verify-image', icon: Fingerprint }
	];
	$: current = items.find((item) =>
		item.href === '/' ? $page.url.pathname === '/' : $page.url.pathname.startsWith(item.href)
	);
	$: title =
		current?.label || ($page.url.pathname.startsWith('/user') ? 'Settings' : 'Image workspace');
	$: if ($page.url.pathname) open = false;
	async function logout() {
		signingOut = true;
		try {
			await fetch('/logout', { method: 'POST' });
			await invalidateAll();
			await goto('/login');
		} finally {
			signingOut = false;
		}
	}
</script>

<div class="app-shell">
	{#if open}<button
			class="sidebar-scrim"
			aria-label="Close navigation"
			on:click={() => (open = false)}
		></button>{/if}
	<aside class:open>
		<div class="side-brand">
			<Brand /><button
				class="icon-btn mobile"
				aria-label="Close navigation"
				on:click={() => (open = false)}><X aria-hidden="true" size={18} /></button
			>
		</div>
		<div class="workspace-switch">
			<span class="workspace-avatar">{user.username.slice(0, 1).toUpperCase()}</span>
			<div class="grow">
				<strong class="truncate">{user.first_name || user.username}'s workspace</strong><small
					>Personal workspace</small
				>
			</div>
		</div>
		<span class="nav-label">WORKSPACE</span>
		<nav aria-label="Workspace">
			{#each items as item}<a
					href={item.href}
					class:active={current?.href === item.href}
					aria-current={current?.href === item.href ? 'page' : undefined}
					><svelte:component
						this={item.icon}
						size={18}
						strokeWidth={1.7}
						aria-hidden="true"
					/>{item.label}</a
				>{/each}
		</nav>
		<div class="side-bottom">
			<div class="private-note">
				<ShieldCheck size={20} aria-hidden="true" /><strong>Your work, your permissions.</strong>
				<p>Choose who gets access to every image you share.</p>
				<a href="/learn/access">Sharing guide <ArrowUpRight aria-hidden="true" size={13} /></a>
			</div>
			<a href="/user" class="settings-link" class:active={$page.url.pathname === '/user'}
				><Settings2 size={18} aria-hidden="true" />Settings</a
			>
			<div class="user-line">
				<div class="user-avatar">{user.username.slice(0, 2).toUpperCase()}</div>
				<div class="grow">
					<strong>{user.username}</strong><small class="truncate">{user.email}</small>
				</div>
				<button class="logout" disabled={signingOut} on:click={logout} aria-label="Sign out"
					><LogOut aria-hidden="true" size={17} /></button
				>
			</div>
		</div>
	</aside>
	<div class="app-main">
		<header class="app-topbar">
			<div class="row">
				<button
					class="icon-btn mobile"
					aria-label="Open navigation"
					aria-expanded={open}
					on:click={() => (open = true)}><Menu aria-hidden="true" size={19} /></button
				><span class="muted small">Workspace</span><ChevronRight
					size={13}
					class="muted"
					aria-hidden="true"
				/><span class="small">{title}</span>
			</div>
			<a class="top-upload" href="/images?upload=1"
				><Plus size={16} aria-hidden="true" /><span>Upload images</span></a
			>
		</header>
		<main id="main" class="workspace-content"><slot /></main>
		<footer class="workspace-footer">
			<span>AuthoGraph workspace</span><a href="/learn/access"
				>Help & documentation <ArrowUpRight aria-hidden="true" size={12} /></a
			>
		</footer>
	</div>
</div>

<style>
	.app-shell {
		min-height: 100vh;
	}
	aside {
		width: 248px;
		position: fixed;
		inset: 0 auto 0 0;
		z-index: 40;
		display: flex;
		flex-direction: column;
		background: white;
		border-right: 1px solid var(--line);
		padding: 28px 18px 0;
	}
	.side-brand {
		padding: 0 10px 28px;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	.workspace-switch {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 13px 10px;
		border: 1px solid var(--line);
		border-radius: 8px;
		margin-bottom: 30px;
	}
	.workspace-avatar {
		width: 32px;
		height: 32px;
		background: #f0eff7;
		display: grid;
		place-items: center;
		border-radius: 7px;
		font-size: 13px;
		font-weight: 700;
	}
	.workspace-switch strong {
		font-size: 12px;
		display: block;
		max-width: 145px;
	}
	.workspace-switch small {
		display: block;
		font-size: 12px;
		color: var(--muted-ink);
		margin-top: 4px;
	}
	.nav-label {
		font-size: 12px;
		letter-spacing: 1.6px;
		font-weight: 700;
		color: var(--muted-ink);
		padding: 0 14px 12px;
	}
	nav {
		display: grid;
		gap: 5px;
	}
	nav a,
	.settings-link {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 13px 14px;
		min-height: 46px;
		color: var(--muted-ink);
		font-weight: 500;
		font-size: 12px;
		border-radius: 7px;
	}
	nav a:hover,
	.settings-link:hover {
		background: var(--paper);
		color: var(--ink);
	}
	nav a.active,
	.settings-link.active {
		background: var(--studio-soft);
		color: var(--studio);
		font-weight: 700;
	}
	.side-bottom {
		margin-top: auto;
		padding-top: 24px;
	}
	.private-note {
		background: #f7f7fc;
		border: 1px solid var(--line);
		border-radius: 10px;
		padding: 16px;
		margin: 16px 4px 20px;
	}
	.private-note > :global(svg) {
		color: var(--studio);
		margin-bottom: 12px;
	}
	.private-note strong {
		display: block;
		font-size: 12px;
	}
	.private-note p {
		font-size: 12px;
		color: var(--muted-ink);
		margin: 8px 0;
	}
	.private-note a {
		font-size: 12px;
		font-weight: 600;
		color: var(--studio);
		display: flex;
		align-items: center;
		gap: 4px;
		min-height: 32px;
	}
	.user-line {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 18px 4px;
		border-top: 1px solid var(--line);
		margin-top: 15px;
	}
	.user-avatar {
		width: 34px;
		height: 34px;
		background: var(--studio-soft);
		color: var(--studio);
		font-size: 12px;
		font-weight: 700;
		display: grid;
		place-items: center;
		border-radius: 50%;
	}
	.user-line strong {
		font-size: 12px;
		display: block;
	}
	.user-line small {
		font-size: 12px;
		color: var(--muted-ink);
		display: block;
		max-width: 120px;
		margin-top: 4px;
	}
	.logout {
		border: 0;
		background: none;
		color: var(--muted-ink);
		width: 36px;
		height: 44px;
		display: grid;
		place-items: center;
	}
	.app-main {
		margin-left: 248px;
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}
	.app-topbar {
		height: 72px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 36px;
		background: rgba(255, 255, 255, 0.94);
		border-bottom: 1px solid var(--line);
	}
	.top-upload {
		display: flex;
		align-items: center;
		gap: 7px;
		font-size: 12px;
		color: var(--studio);
		font-weight: 700;
		min-height: 44px;
	}
	.workspace-content {
		padding: 36px;
		max-width: 1600px;
		width: 100%;
		margin: 0 auto;
		flex: 1;
	}
	.workspace-footer {
		display: flex;
		justify-content: space-between;
		margin: 0 36px;
		padding: 24px 0;
		color: var(--muted-ink);
		font-size: 12px;
		border-top: 1px solid var(--line);
	}
	.workspace-footer a {
		display: flex;
		align-items: center;
		gap: 5px;
	}
	.mobile {
		display: none;
	}
	.sidebar-scrim {
		position: fixed;
		inset: 0;
		background: #20212d66;
		z-index: 39;
		border: 0;
	}
	@media (max-height: 780px) {
		.private-note {
			display: none;
		}
	}
	@media (max-width: 1050px) {
		aside {
			width: 220px;
			padding-left: 12px;
			padding-right: 12px;
		}
		.app-main {
			margin-left: 220px;
		}
		.workspace-content {
			padding: 28px;
		}
		.app-topbar {
			padding: 0 28px;
		}
		.workspace-switch strong {
			max-width: 128px;
		}
	}
	@media (max-width: 800px) {
		aside {
			transform: translateX(-100%);
			width: 260px;
			transition: transform 0.2s;
		}
		.open {
			transform: translateX(0);
		}
		.app-main {
			margin: 0;
		}
		.mobile {
			display: grid;
		}
		.workspace-content {
			padding: 24px 20px;
		}
		.app-topbar {
			height: 64px;
			padding: 0 20px;
		}
		.app-topbar > .row {
			gap: 8px;
		}
		.workspace-footer {
			margin: 0 20px;
		}
		.top-upload span {
			display: none;
		}
		.top-upload {
			width: 44px;
			justify-content: center;
		}
		.private-note {
			display: block;
		}
	}
</style>
