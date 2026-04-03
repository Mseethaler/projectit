<template>
    <div class="pt-6 pl-6 pr-6 font-[Inter]">
        <div v-if="loading" class="flex h-80 items-center justify-center">
            <Spinner class="h-12"></Spinner>
        </div>
        <div v-else-if="!route" class="pt-3 pb-4 border-2 border-[#B9C8EA] text-center rounded-lg bg-[#D6E1F9] font-[600]">
            No route assigned for today.
        </div>
        <div v-else>
            <div class="pb-4">
                <p class="text-[#4A6BB6] font-[700] text-lg">Today's Route</p>
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
                            <p class="text-sm text-gray-500">{{ stop.address_display }}</p>
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
import { ref, inject, watch } from 'vue'
import { createResource, Spinner } from 'frappe-ui'
import { useRouter } from 'vue-router'
import StatusBadge from './StatusBadge.vue'

const router = useRouter()
const employee = inject('employee_id')
const route = ref(null)
const loading = ref(true)

const routeResource = createResource({
    url: 'projectit.api.get_todays_route',
    makeParams() {
        return { employee_id: employee.name }
    },
    onSuccess(data) {
        console.log('RouteIT data received:', JSON.stringify(data))
        route.value = data
        loading.value = false
    },
    onError(err) {
        console.log('RouteIT error:', err)
        loading.value = false
    },
})

watch(() => employee.name, (name) => {
    if (name) {
        routeResource.fetch()
    }
}, { immediate: true })

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
