<script setup lang="ts">
defineProps<{
  name: "leaf" | "people" | "hospital" | "truck" | "shield" | "heart";
  size?: number;
}>();
</script>

<template>
  <svg
    :width="size ?? 20"
    :height="size ?? 20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'leaf'">
      <path d="M5 19c9 0 15-5 15-15-10 0-15 5-15 15Z" />
      <path d="M5 19c3-3 7-6 11-8" />
    </template>
    <template v-else-if="name === 'people'">
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5" />
      <circle cx="17" cy="9" r="2.4" />
      <path d="M15.5 14.2c2.4.2 4.2 1.8 4.7 4.8" />
    </template>
    <template v-else-if="name === 'hospital'">
      <path d="M4 21V7l8-4 8 4v14" />
      <path d="M9 21v-5h6v5" />
      <path d="M12 8v4M10 10h4" />
    </template>
    <template v-else-if="name === 'truck'">
      <path d="M3 7h11v9H3z" />
      <path d="M14 10h4l3 3v3h-7z" />
      <circle cx="7" cy="18" r="1.6" />
      <circle cx="17.5" cy="18" r="1.6" />
    </template>
    <template v-else-if="name === 'shield'">
      <path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6l7-3Z" />
      <path d="M9 12l2 2 4-4" />
    </template>
    <template v-else>
      <path d="M12 20s-7-4.4-7-9a4 4 0 0 1 7-2.6A4 4 0 0 1 19 11c0 4.6-7 9-7 9Z" />
    </template>
  </svg>
</template>
