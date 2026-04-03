<template>
    <span :class="[
        'text-xs font-[600] px-2 py-1 rounded-full',
        status === 'Complete' ? 'bg-green-100 text-green-700' :
        status === 'In Progress' ? 'bg-[#4A6BB6] text-white' :
        status === 'OMW' ? 'bg-yellow-100 text-yellow-700' :
        'bg-gray-100 text-gray-500'
    ]">
        {{ status || 'Pending' }}
    </span>
</template>
<script setup>
defineProps({
    status: String
})
</script>
