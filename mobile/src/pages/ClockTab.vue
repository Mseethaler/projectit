<template>
    <div class="pt-6 pl-6 pr-6 font-[Inter]">
        <div v-if="loading" class="flex h-80 items-center justify-center">
            <Spinner class="h-12"></Spinner>
        </div>
        <div v-else class="flex flex-col gap-6">

            <!-- Clock Status Card -->
            <div class="border-2 border-[#B9C8EA] rounded-lg bg-[#F5F8FF] pt-4 pb-4 pl-4 pr-4">
                <p class="text-[#4A6BB6] font-[700] text-lg pb-3">Today's Clock</p>

                <div v-if="clockStatus.clocked_in" class="flex flex-col gap-2">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-500">First Clock In</span>
                        <span class="font-[600]">
                            {{ dayjs(clockStatus.checkin_time).format('hh:mm A') }}
                        </span>
                    </div>
                    <div v-if="clockStatus.clocked_out" class="flex justify-between text-sm">
                        <span class="text-gray-500">Last Clock Out</span>
                        <span class="font-[600]">
                            {{ dayjs(clockStatus.checkout_time).format('hh:mm A') }}
                        </span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-500">Billed Hours</span>
                        <span class="font-[600]">{{ clockStatus.total_billed_hours || 0 }} hrs</span>
                    </div>
                </div>
                <div v-else class="text-sm text-gray-500">
                    Not clocked in yet today.
                </div>
            </div>

            <!-- Start Day Button — show if not currently clocked in -->
            <div v-if="!clockStatus.currently_in">
                <PrimaryButton
                    name="Start Day"
                    :loading="actionLoading"
                    @click="startDay"
                ></PrimaryButton>
            </div>

            <!-- End Day Button — show if currently clocked in -->
            <div v-else>
                <div class="pb-2 text-sm text-gray-500">
                    {{ elapsedTime }} since last clock-in
                </div>
                <PrimaryButton
                    name="End Day"
                    :loading="actionLoading"
                    @click="endDay"
                ></PrimaryButton>
            </div>

        </div>
    </div>

    <div v-if="showError">
        <ErrorMessage
            @dialog-event="showError = $event"
            :error-message="errorMessage"
        ></ErrorMessage>
    </div>
</template>
<script setup>
import { ref, computed, inject, watch } from 'vue'
import { createResource, Spinner, toast } from 'frappe-ui'
import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'
import PrimaryButton from '../components/PrimaryButton.vue'
import ErrorMessage from '../components/ErrorMessage.vue'

dayjs.extend(duration)

const employee = inject('employee_id')
const loading = ref(true)
const actionLoading = ref(false)
const showError = ref(false)
const errorMessage = ref('')
const clockStatus = ref({
    clocked_in: false,
    currently_in: false,
    clocked_out: false,
    checkin_time: null,
    checkout_time: null,
    total_billed_hours: 0,
})

const elapsedTime = computed(() => {
    if (!clockStatus.value.checkin_time) return ''
    const diff = dayjs().diff(dayjs(clockStatus.value.checkin_time))
    const d = dayjs.duration(diff)
    return `${Math.floor(d.asHours())}h ${d.minutes()}m`
})

const statusResource = createResource({
    url: 'projectit.api.get_clock_status',
    makeParams() {
        return { employee_id: employee.name }
    },
    onSuccess(data) {
        clockStatus.value = data
        loading.value = false
    },
    onError() {
        loading.value = false
    },
})

watch(() => employee.name, (name) => {
    if (name) statusResource.fetch()
}, { immediate: true })

function getLocation(callback) {
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (pos) => callback(pos.coords.latitude, pos.coords.longitude),
            (err) => {
                errorMessage.value = err.message
                showError.value = true
                actionLoading.value = false
            }
        )
    } else {
        callback(null, null)
    }
}

const startDayResource = createResource({
    url: 'projectit.api.start_day',
    onSuccess(data) {
        toast({
            title: 'Clocked In',
            text: `Started at ${dayjs(data.time).format('hh:mm A')}`,
            icon: 'check-circle',
            position: 'bottom-center',
            iconClasses: 'text-blue-500',
        })
        actionLoading.value = false
        statusResource.fetch()
    },
    onError(e) {
        errorMessage.value = e
        showError.value = true
        actionLoading.value = false
    },
})

const endDayResource = createResource({
    url: 'projectit.api.end_day',
    onSuccess(data) {
        toast({
            title: 'Clocked Out',
            text: `Ended at ${dayjs(data.time).format('hh:mm A')}`,
            icon: 'check-circle',
            position: 'bottom-center',
            iconClasses: 'text-blue-500',
        })
        actionLoading.value = false
        statusResource.fetch()
    },
    onError(e) {
        errorMessage.value = e
        showError.value = true
        actionLoading.value = false
    },
})

function startDay() {
    actionLoading.value = true
    getLocation((lat, lng) => {
        startDayResource.fetch({
            employee_id: employee.name,
            latitude: lat,
            longitude: lng,
        })
    })
}

function endDay() {
    actionLoading.value = true
    getLocation((lat, lng) => {
        endDayResource.fetch({
            employee_id: employee.name,
            latitude: lat,
            longitude: lng,
        })
    })
}
</script>
