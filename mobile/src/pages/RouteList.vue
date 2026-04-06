<template>
    <div class="pt-6 pl-6 pr-6 font-[Inter]">

        <!-- Date Selector -->
        <div class="flex items-center justify-between mb-5">
            <button
                @click="changeDate(-1)"
                class="text-[#4A6BB6] p-2 rounded-lg bg-[#F5F8FF] border-2 border-[#B9C8EA]"
            >
                <FeatherIcon name="chevron-left" class="h-5 w-5" />
            </button>

            <div class="relative flex-1 mx-3 text-center">
                <span class="font-[600] text-[#4A6BB6] pointer-events-none">
                    {{ formattedDate }}
                </span>
                <input
                    type="date"
                    :value="selectedDate"
                    @change="onDateChange"
                    class="absolute inset-0 opacity-0 w-full h-full cursor-pointer"
                />
            </div>

            <button
                @click="changeDate(1)"
                class="text-[#4A6BB6] p-2 rounded-lg bg-[#F5F8FF] border-2 border-[#B9C8EA]"
            >
                <FeatherIcon name="chevron-right" class="h-5 w-5" />
            </button>
        </div>

        <div v-if="loading" class="flex h-80 items-center justify-center">
            <Spinner class="h-12"></Spinner>
        </div>
        <div v-else-if="!route" class="pt-3 pb-4 border-2 border-[#B9C8EA] text-center rounded-lg bg-[#D6E1F9] font-[600]">
            No route assigned for {{ formattedDate }}.
        </div>
        <div v-else>
            <div class="pb-4">
                <p class="text-[#4A6BB6] font-[700] text-lg">Route</p>
                <p class="text-sm text-gray-500">{{ route.stops.length }} stops</p>
            </div>
            <div class="flex flex-col gap-3">
                <div
                    v-for="stop in route.stops"
                    :key="stop.name"
                    @click="openStop(stop)"
                    :class="[
                        'rounded-lg border-2 p-4 flex items-center justify-between cursor-pointer',
                        stop.custom_status === 'Complete'
                            ? 'border-green-300 bg-green-50'
                            : stop.custom_status === 'In Progress'
                            ? 'border-[#4A6BB6] bg-[#D6E1F9]'
                            : stop.custom_status === 'OMW'
                            ? 'border-yellow-300 bg-yellow-50'
                            : 'border-[#B9C8EA] bg-white'
                    ]"
                >
                    <div class="flex items-center gap-3">
                        <div class="text-[#4A6BB6] font-[700] text-lg w-6 text-center">
                            {{ stop.idx }}
                        </div>
                        <div>
                            <p class="font-[600]">{{ stop.customer }}</p>
                            <p class="text-sm text-gray-500" v-html="stop.address_display"></p>
                        </div>
                    </div>
                    <div>
                        <StatusBadge :status="stop.custom_status"></StatusBadge>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script setup>
import { ref, inject, watch, computed, onMounted, onUnmounted } from 'vue'
import { createResource, Spinner, FeatherIcon } from 'frappe-ui'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import StatusBadge from './StatusBadge.vue'

const POLL_INTERVAL_MS = 3 * 60 * 1000 // 3 minutes

const router = useRouter()
const employee = inject('employee_id')
const route = ref(null)
const loading = ref(true)
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
let poller = null

const formattedDate = computed(() => {
    const d = dayjs(selectedDate.value)
    const today = dayjs().format('YYYY-MM-DD')
    const yesterday = dayjs().subtract(1, 'day').format('YYYY-MM-DD')
    const tomorrow = dayjs().add(1, 'day').format('YYYY-MM-DD')
    if (selectedDate.value === today) return 'Today'
    if (selectedDate.value === yesterday) return 'Yesterday'
    if (selectedDate.value === tomorrow) return 'Tomorrow'
    return d.format('ddd, MMM D')
})

const routeResource = createResource({
    url: 'projectit.api.get_todays_route',
    makeParams() {
        return {
            employee_id: employee.name,
            selected_date: selectedDate.value,
        }
    },
    onSuccess(data) {
        route.value = data
        loading.value = false
    },
    onError() {
        loading.value = false
    },
})

function fetchRoute() {
    loading.value = true
    route.value = null
    routeResource.fetch()
}

function silentRefresh() {
    // Refresh without resetting the loading state or clearing the route
    // so the UI doesn't flash while polling
    routeResource.fetch()
}

watch(() => employee.name, (name) => {
    if (name) fetchRoute()
}, { immediate: true })

watch(selectedDate, () => {
    if (employee.name) fetchRoute()
})

onMounted(() => {
    poller = setInterval(() => {
        if (employee.name) silentRefresh()
    }, POLL_INTERVAL_MS)
})

onUnmounted(() => {
    clearInterval(poller)
})

function changeDate(days) {
    selectedDate.value = dayjs(selectedDate.value).add(days, 'day').format('YYYY-MM-DD')
}

function onDateChange(e) {
    if (e.target.value) {
        selectedDate.value = e.target.value
    }
}

function openStop(stop) {
    router.push({
        name: 'StopDetail',
        params: {
            trip_name: route.value.name,
            stop_name: stop.name,
        },
    })
}
</script>
