<script lang="ts">
	import { page } from '$app/stores';
	import { goto, invalidateAll } from '$app/navigation';
	import type { PageData } from './$types';
	import ImageGrid from '$lib/product/ImageGrid.svelte';
	import Upload from '$lib/product/Upload.svelte';
	import Empty from '$lib/product/Empty.svelte';
	import { Plus, Search, ChevronLeft, ChevronRight } from 'lucide-svelte';
	export let data: PageData;
	let showUpload = false;
	let search = '';
	$: search = $page.url.searchParams.get('search') || '';
	$: if ($page.url.searchParams.get('upload') === '1') showUpload = true;
	$: current = Number($page.url.searchParams.get('page') || 1);
	$: pages = Math.max(1, Math.ceil(data.images.count / 24));
	function query(key: string, value: string) {
		const params = new URLSearchParams($page.url.searchParams);
		params.delete('upload');
		params.set(key, value);
		if (key !== 'page') params.set('page', '1');
		goto(`?${params}`);
	}
	async function uploaded() {
		showUpload = false;
		const params = new URLSearchParams($page.url.searchParams);
		params.delete('upload');
		await goto(`/images?${params}`);
		await invalidateAll();
	}
</script>

<svelte:head><title>Image library · AuthoGraph</title></svelte:head>
<div class="page-heading">
	<div>
		<h1>Image library</h1>
		<p>A private home for your originals. Ready when you are.</p>
	</div>
	<button class="btn primary" on:click={() => (showUpload = !showUpload)}
		><Plus aria-hidden="true" size={17} />Upload images</button
	>
</div>
{#if showUpload}<Upload
		on:complete={uploaded}
		on:partial={() => invalidateAll()}
		on:close={() => {
			showUpload = false;
			const params = new URLSearchParams($page.url.searchParams);
			params.delete('upload');
			goto(`?${params}`, { replaceState: true });
		}}
	/>{/if}
<form class="toolbar" on:submit|preventDefault={() => query('search', search)}>
	<div class="search">
		<Search aria-hidden="true" size={17} /><input
			aria-label="Search image names"
			placeholder="Search your images…"
			bind:value={search}
		/>
	</div>
	<button class="btn" type="submit">Search</button>
	<div class="grow"></div>
	<label class="sr-only" for="sort">Sort images</label><select
		id="sort"
		class="input"
		value={$page.url.searchParams.get('sort') || '-created_at'}
		on:change={(e) => query('sort', e.currentTarget.value)}
		><option value="-created_at">Newest first</option><option value="created_at"
			>Oldest first</option
		><option value="image_name">Name: A–Z</option><option value="-file_size">Largest first</option
		></select
	><label class="sr-only" for="format">Image format</label><select
		id="format"
		class="input"
		value={$page.url.searchParams.get('file_type') || ''}
		on:change={(e) => query('file_type', e.currentTarget.value)}
		><option value="">All formats</option><option value="jpeg">JPEG</option><option value="png"
			>PNG</option
		><option value="webp">WebP</option></select
	>
</form>
<div class="section-heading">
	<span class="small muted">{data.images.count} {data.images.count === 1 ? 'image' : 'images'}</span
	><span class="badge"><span aria-hidden="true">●</span> Private library</span>
</div>
{#if data.images.results.length}<ImageGrid images={data.images.results} />{:else}<div class="panel">
		<Empty
			title={search ? 'No matching images' : 'Make room for your best work'}
			description={search
				? 'Try a different image name or clear your filters.'
				: 'Upload your first image. Originals stay private until you choose to share them.'}
			href={search ? '/images' : '/images?upload=1'}
			action={search ? 'Clear filters' : 'Upload your first image'}
		/>
	</div>{/if}{#if pages > 1}<div class="pagination">
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
