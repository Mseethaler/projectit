<template>
    <div class="pt-6 pl-6 pr-6 font-[Inter]">
        <div v-if="loading" class="flex h-80 items-center justify-center">
            <Spinner class="h-12"></Spinner>
        </div>
        <div v-else-if="!entries.length" class="pt-3 pb-4 border-2 border-[#B9C8EA] text-center rounded-lg bg-[#D6E1F9] font-[600]">
            No clock entries found.
        </div>
        <div v-else class="flex flex-col gap-3">
            <div
                v-for="entry in entries"
                :key="entry.date"
                class="rounded-lg border-2 border-[#B9C8EA] bg-[#F5F8FF] p-4"
            >
                <div class="flex justify-between items-center mb-2">
                    <span class="font-[700] text-[#4A6BB6]">{{ formatDate(entry.date) }}</span>
                    <span class="font-[700] text-gray-700">{{ entry.hours }} hrs</span>
                </div>
                <div class="flex justify-between text-sm text-gray-500">
                    <div class="flex items-center gap-1">
                        <FeatherIcon name="log-in" class="h-4 w-4 text-green-500" />
                        <span>{{ entry.clock_in || '—' }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <FeatherIcon name="log-out" class="h-4 w-4 text-red-400" />
                        <span>{{ entry.clock_out || '—' }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script setup>
import { ref, inject, watch } from 'vue'
import { createResource, Spinner, FeatherIcon } from 'frappe-ui'
import dayjs from 'dayjs'

const employee = inject('employee_id')
const loading = ref(true)
const entries = ref([])

const entriesResource = createResource({
    url: 'projectit.api.get_attendance_entries',
    makeParams() {
        return { employee_id: employee.name }
    },
    onSuccess(data) {
        entries.value = data
        loading.value = false
    },
    onError() {
        loading.value = false
    },
})

watch(() => employee.name, (name) => {
    if (name) entriesResource.fetch()
}, { immediate: true })

function formatDate(dateStr) {
    const d = dayjs(dateStr)
    const today = dayjs().format('YYYY-MM-DD')
    const yesterday = dayjs().subtract(1, 'day').format('YYYY-MM-DD')
    if (dateStr === today) return 'Today'
    if (dateStr === yesterday) return 'Yesterday'
    return d.format('ddd, MMM D')
}
</script>
