<script lang="ts">
	import { LockKeyhole, ArrowUpRight } from 'lucide-svelte';
	import type { ImageItem } from '$lib/types';
	import { bytes } from './api';
	export let images: ImageItem[] = [];
</script>

<div class="photo-grid">
	{#each images as image, i (image.id)}<a class="photo-card" href={`/images/${image.id}`}
			><div class="photo-thumb">
				<img
					src={image.image_url}
					alt={image.image_name}
					loading="lazy"
					width="640"
					height="480"
				/><span class="photo-index">{String(i + 1).padStart(2, '0')}</span>
			</div>
			<div class="photo-info">
				<h3 class="truncate">{image.image_name}</h3>
				<small
					>{image.file_type.toUpperCase()} <span aria-hidden="true">·</span>
					{bytes(image.file_size)}</small
				>
				<div class="row">
					<span class:green={image.access_control_enabled} class="badge"
						><LockKeyhole size={11} aria-hidden="true" />{image.access_control_enabled
							? 'Shared privately'
							: 'Only you'}</span
					><ArrowUpRight size={15} class="muted" aria-hidden="true" />
				</div>
			</div></a
		>{/each}
</div>
