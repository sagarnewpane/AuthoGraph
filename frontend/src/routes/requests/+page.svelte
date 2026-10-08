<script lang="ts">
	import type { PageData } from './$types';
	import Records from '$lib/product/Records.svelte';
	export let data: PageData;
</script>

<Records kind="requests" records={data.records} />
