<script lang="ts">
	import AuthPage from '$lib/product/AuthPage.svelte';
	import type { ActionData } from './$types';
	export let form: ActionData;
</script>

<AuthPage mode="reset" {form} />
