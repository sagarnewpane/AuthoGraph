<script lang="ts">
	import { ImagePlus } from 'lucide-svelte';
	export let title = 'Your workspace starts here';
	export let description = 'Upload your first image to start protecting and sharing your work.';
	export let href = '/images?upload=1';
	export let action = 'Upload images';
</script>

<div class="empty">
	<div class="empty-icon"><ImagePlus size={25} aria-hidden="true" /></div>
	<h3>{title}</h3>
	<p>{description}</p>
	{#if action}<a class="btn primary" {href}>{action}</a>{/if}
</div>
