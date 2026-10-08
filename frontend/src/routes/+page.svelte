<script lang="ts">
	import type { PageData } from './$types';
	import Landing from '$lib/product/Landing.svelte';
	import ImageGrid from '$lib/product/ImageGrid.svelte';
	import Empty from '$lib/product/Empty.svelte';
	import { bytes, date } from '$lib/product/api';
	import {
		Plus,
		ArrowUpRight,
		Images,
		Link2,
		Eye,
		HardDrive,
		ArrowRight,
		LockKeyhole
	} from 'lucide-svelte';
	export let data: PageData;
</script>

<svelte:head
	><title
		>{data.workspace
			? 'Overview · AuthoGraph'
			: 'AuthoGraph — Your work, shared on your terms'}</title
	></svelte:head
>
{#if data.workspace}<div class="page-heading">
		<div>
			<div class="eyebrow" style="margin-bottom:10px">YOUR CREATIVE WORKSPACE</div>
			<h1>Welcome back{data.user?.first_name ? `, ${data.user.first_name}` : ''}.</h1>
			<p>A little clarity on your images, links, and recent activity.</p>
		</div>
		<a class="btn primary" href="/images?upload=1"
			><Plus aria-hidden="true" size={17} />Upload images</a
		>
	</div>
	<div class="stack">
		<div class="stat-grid">
			{#each [{ label: 'Images in your library', value: data.workspace.images, note: 'Originals stored privately', icon: Images }, { label: 'Active share links', value: data.workspace.active_links, note: 'Available to your recipients', icon: Link2 }, { label: 'Verified views', value: data.workspace.views, note: 'Recorded through your links', icon: Eye }, { label: 'Storage used', value: bytes(data.workspace.storage_bytes), note: `of ${bytes(data.workspace.storage_limit)} available`, icon: HardDrive }] as stat}<div
					class="stat"
				>
					<div class="stat-top">
						<span>{stat.label}</span><svelte:component
							this={stat.icon}
							aria-hidden="true"
							size={17}
							strokeWidth={1.6}
						/>
					</div>
					<div class="stat-value">{stat.value}</div>
					<div class="stat-note">{stat.note}</div>
				</div>{/each}
		</div>
		<section class="studio-banner">
			<div class="banner-symbol"><LockKeyhole aria-hidden="true" size={27} /></div>
			<div class="grow">
				<h2>Good work deserves thoughtful sharing.</h2>
				<p>Start with an image. Add your protection. Share it with the right people.</p>
			</div>
			<a href="/learn/access" class="btn"
				>Explore the guide <ArrowUpRight aria-hidden="true" size={15} /></a
			>
		</section>
		<section>
			<div class="section-heading">
				<h2>Recent images <span class="count">{data.workspace.images}</span></h2>
				<a href="/images" class="text-link"
					>View library <ArrowRight aria-hidden="true" size={15} /></a
				>
			</div>
			{#if data.images?.results.length}<ImageGrid images={data.images.results} />{:else}<div
					class="panel"
				>
					<Empty />
				</div>{/if}
		</section>
		<div class="two-col">
			<section class="panel">
				<div class="panel-head">
					<h2>Recent activity</h2>
					<a href="/activity" class="text-link"
						>View all <ArrowUpRight aria-hidden="true" size={14} /></a
					>
				</div>
				{#if data.activity?.results.length}<div class="activity-list">
						{#each data.activity.results as item}<div class="activity-row">
								<span class:failed={!item.success} class="activity-icon"
									><Eye aria-hidden="true" size={17} /></span
								>
								<div class="grow">
									<strong>{item.email}</strong>
									<p>{item.success ? item.action_type : 'Attempted access'} · {item.image_name}</p>
								</div>
								<small>{date(item.accessed_at)}</small>
							</div>{/each}
					</div>{:else}<Empty
						title="No activity yet"
						description="Verified views and downloads will appear here once you share an image."
						action=""
					/>{/if}
			</section>
			<section class="panel">
				<div class="panel-head">
					<h2>Access requests</h2>
					<span class="badge purple">{data.workspace.pending_requests} pending</span>
				</div>
				{#if data.requests?.results.length}<div class="panel-pad stack">
						{#each data.requests.results as request}<div>
								<h3 class="truncate">{request.email}</h3>
								<p class="muted small">{request.image_name}</p>
							</div>{/each}<a href="/requests" class="btn"
							>Review requests <ArrowRight aria-hidden="true" size={15} /></a
						>
					</div>{:else}<Empty
						title="You're all caught up"
						description="Requests from people outside your recipient list will appear here."
						action=""
					/>{/if}
			</section>
		</div>
	</div>{:else}<Landing />{/if}

<style>
	.studio-banner {
		display: flex;
		align-items: center;
		gap: 20px;
		padding: 28px;
		background: #f0eefb;
		border: 1px solid #e3dff6;
		border-radius: 12px;
	}
	.studio-banner h2 {
		font-size: 17px;
	}
	.studio-banner p {
		font-size: 12px;
		color: #68617f;
		margin-top: 7px;
	}
	.banner-symbol {
		height: 56px;
		width: 56px;
		border: 1px solid #d9d3f5;
		background: #fff8;
		color: var(--studio);
		border-radius: 14px;
		display: grid;
		place-items: center;
	}
	.studio-banner .btn {
		background: transparent;
		border-color: #d8d2f0;
		font-size: 12px;
	}
	.count {
		color: var(--muted-ink);
		font-size: 12px;
		font-weight: 500;
		margin-left: 8px;
	}
	.activity-row {
		display: flex;
		gap: 12px;
		align-items: center;
		padding: 19px 24px;
		border-bottom: 1px solid var(--line);
	}
	.activity-row:last-child {
		border: 0;
	}
	.activity-icon {
		width: 34px;
		height: 34px;
		display: grid;
		place-items: center;
		background: var(--positive-soft);
		color: var(--positive);
		border-radius: 50%;
	}
	.activity-icon.failed {
		background: var(--danger-soft);
		color: var(--danger);
	}
	.activity-row strong {
		font-size: 12px;
		word-break: break-word;
	}
	.activity-row p {
		font-size: 12px;
		color: var(--muted-ink);
		margin-top: 4px;
	}
	.activity-row small {
		font-size: 12px;
		color: var(--muted-ink);
		white-space: nowrap;
	}
	@media (max-width: 1000px) {
		.studio-banner {
			flex-wrap: wrap;
		}
		.studio-banner .grow {
			flex-basis: 70%;
		}
	}
	@media (max-width: 480px) {
		.banner-symbol {
			display: none;
		}
		.studio-banner {
			padding: 20px;
		}
		.activity-row {
			padding: 16px;
		}
		.activity-row small {
			display: none;
		}
	}
</style>
