<template>
    <div class="font-[Inter]">
        <div v-if="uploading" class="flex h-80 items-center justify-center">
            <Spinner class="h-12"></Spinner>
        </div>
        <div v-else>
            <!-- Header -->
            <div class="pt-4 pl-6 pr-6 flex items-center gap-3">
                <p class="text-[#4A6BB6] font-[700] text-lg">{{ stop.customer }}</p>
            </div>

            <!-- Address -->
            <div class="pt-4 pl-6 pr-6">
                <div
                    class="bg-[#B9C8EA] pt-3 pb-3 pl-4 pr-3 rounded-t-md flex justify-between items-center"
                >
                    <div>
                        <p class="text-[#4A6BB6] font-[600]">{{ stop.customer }}</p>
                        <p class="text-sm text-gray-600" v-html="stop.address_display"></p>
                    </div>
                    <StatusBadge :status="stop.custom_status"></StatusBadge>
                </div>
                <div
                    class="bg-[#F5F8FF] pl-4 pr-3 pt-4 pb-4 rounded-b-md border-[#B9C8EA] border-x-2 border-b-2 flex flex-col gap-3"
                >
                    <!-- Open Maps -->
                    <button
                        @click="openMaps"
                        class="flex items-center gap-2 text-[#4A6BB6] font-[600]"
                    >
                        <FeatherIcon name="map-pin" class="h-5 w-5" />
                        <span>Open in Maps</span>
                    </button>

                    <!-- Grand Total -->
                    <div v-if="stop.grand_total" class="text-sm text-gray-600">
                        Job Total: <span class="font-[600]">${{ stop.grand_total }}</span>
                    </div>

                    <!-- Estimated Arrival -->
                    <div v-if="stop.estimated_arrival" class="text-sm text-gray-600">
                        Est. Arrival:
                        <span class="font-[600]">{{
                            dayjs(stop.estimated_arrival).format('hh:mm A')
                        }}</span>
                    </div>

                    <!-- Special Instructions -->
                    <div v-if="stop.special_instructions" class="text-sm border-t border-[#B9C8EA] pt-3 mt-1">
                        <div class="flex items-center gap-1 text-[#4A6BB6] font-[600] mb-1">
                            <FeatherIcon name="info" class="h-4 w-4" />
                            <span>Special Instructions</span>
                        </div>
                        <p class="text-gray-700">{{ stop.special_instructions }}</p>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-6 pl-6 pr-6 flex flex-col gap-4">

                <!-- OMW -->
                <div v-if="stop.custom_status === 'Pending'">
                    <PrimaryButton
                        name="On My Way"
                        :loading="actionLoading"
                        @click="openSmsPrompt('omw')"
                        class="w-full"
                    ></PrimaryButton>
                </div>

                <!-- Check In -->
                <div v-if="stop.custom_status === 'OMW'">
                    <PrimaryButton
                        name="Check In"
                        :loading="actionLoading"
                        @click="showCamera = true; cameraMode = 'Check-In'"
                        class="w-full"
                    ></PrimaryButton>
                </div>

                <!-- Check Out -->
                <div v-if="stop.custom_status === 'In Progress'">
                    <div class="text-sm text-gray-500 pb-2">
                        Checked in at {{ dayjs(stop.custom_checkin_time).format('hh:mm A') }}
                    </div>
                    <PrimaryButton
                        name="Check Out"
                        :loading="actionLoading"
                        @click="showCamera = true; cameraMode = 'Check-Out'"
                        class="w-full"
                    ></PrimaryButton>
                </div>

                <!-- Complete -->
                <div
                    v-if="stop.custom_status === 'Complete'"
                    class="pt-3 pb-4 border-2 border-green-300 text-center rounded-lg bg-green-50 font-[600] text-green-700"
                >
                    ✓ Job Complete
                    <div class="text-sm font-[400] text-gray-500 pt-1">
                        {{ dayjs(stop.custom_checkin_time).format('hh:mm A') }} —
                        {{ dayjs(stop.custom_checkout_time).format('hh:mm A') }}
                    </div>
                </div>
            </div>
        </div>

        <!-- SMS Prompt Modal -->
        <div
            v-if="showSmsPrompt"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-end z-50"
            @click.self="showSmsPrompt = false"
        >
            <div class="bg-white w-full rounded-t-2xl p-6 flex flex-col gap-4">
                <div class="flex justify-between items-center">
                    <p class="font-[700] text-[#4A6BB6] text-lg">Send Message</p>
                    <button @click="showSmsPrompt = false" class="text-gray-400">
                        <FeatherIcon name="x" class="h-5 w-5" />
                    </button>
                </div>
                <div v-if="stop.phone" class="text-sm text-gray-500">
                    To: {{ stop.customer }} ({{ stop.phone }})
                </div>
                <div v-else class="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                    No phone number on file. Status will update without sending SMS.
                </div>
                <textarea
                    v-model="smsMessage"
                    class="w-full border-2 border-[#B9C8EA] rounded-lg p-3 text-sm font-[Inter] resize-none"
                    rows="4"
                ></textarea>
                <div class="flex gap-3">
                    <button
                        @click="skipSms"
                        class="flex-1 border-2 border-[#B9C8EA] rounded-lg py-2 text-gray-500 font-[600]"
                    >
                        Skip
                    </button>
                    <button
                        @click="sendSms"
                        :disabled="smsLoading"
                        class="flex-1 bg-[#4A6BB6] rounded-lg py-2 text-white font-[600] disabled:bg-gray-300"
                    >
                        {{ smsLoading ? 'Sending...' : 'Send' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Camera -->
        <Camera v-if="showCamera"></Camera>

        <!-- Error -->
        <div v-if="showError">
            <ErrorMessage
                @dialog-event="showError = $event"
                :error-message="errorMessage"
            ></ErrorMessage>
        </div>
    </div>
</template>
<script setup>
import { ref, onMounted, inject, watch } from 'vue'
import { createResource, Spinner, FeatherIcon, toast } from 'frappe-ui'
import { useRouter, useRoute } from 'vue-router'
import dayjs from 'dayjs'
import PrimaryButton from '../components/PrimaryButton.vue'
import ErrorMessage from '../components/ErrorMessage.vue'
import Camera from '../components/Camera.vue'
import StatusBadge from './StatusBadge.vue'
import { showCamera, cameraMode, imageFile } from '../data/camera_context'
import { FileAttachment } from '../composables'

const router = useRouter()
const route = useRoute()
const employee = inject('employee_id')

const trip_name = route.params.trip_name
const stop_name = route.params.stop_name

const stop = ref({})
const uploading = ref(false)
const actionLoading = ref(false)
const errorMessage = ref('')
const showError = ref(false)

// SMS prompt state
const showSmsPrompt = ref(false)
const smsMessage = ref('')
const smsLoading = ref(false)
const pendingSmsType = ref('') // 'omw' or 'complete'

// Watch for photo capture
watch(imageFile, () => {
    if (imageFile.value) {
        handleImageCapture(imageFile.value)
    }
})

// Load stop data
const stopResource = createResource({
    url: 'projectit.api.get_todays_route',
    makeParams() {
        return { employee_id: employee.name }
    },
    onSuccess(data) {
        if (data && data.stops) {
            const found = data.stops.find((s) => s.name === stop_name)
            if (found) stop.value = found
        }
    },
})

onMounted(() => {
    stopResource.fetch()
})

function openMaps() {
    const rawAddress = (stop.value.customer_address || stop.value.address || '')
        .replace(/<[^>]*>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
    window.open(`https://maps.google.com/?q=${encodeURIComponent(rawAddress)}`, '_blank')
}

function openSmsPrompt(type) {
    pendingSmsType.value = type
    const techName = employee.employee_name || 'Your technician'
    const company = employee.company || ''
    const customer = stop.value.customer || 'there'

    if (type === 'omw') {
        smsMessage.value = `Hi ${customer}, this is ${techName}${company ? ' from ' + company : ''}. I'm on my way to your location!`
    } else {
        smsMessage.value = `Hi ${customer}, your service has been completed. Thank you for choosing ${company || 'us'}!`
    }
    showSmsPrompt.value = true
}

function skipSms() {
    showSmsPrompt.value = false
    if (pendingSmsType.value === 'omw') {
        updateStatus('OMW')
    }
    // checkout skip — status already updated by handleImageCapture
}

const smsResource = createResource({
    url: 'projectit.api.send_route_sms',
    onSuccess() {
        smsLoading.value = false
        showSmsPrompt.value = false
        toast({
            title: 'Message Sent',
            icon: 'check-circle',
            position: 'bottom-center',
            iconClasses: 'text-blue-500',
        })
        if (pendingSmsType.value === 'omw') {
            updateStatus('OMW')
        }
    },
    onError(e) {
        smsLoading.value = false
        showSmsPrompt.value = false
        // Don't block flow on SMS failure — still update status
        if (pendingSmsType.value === 'omw') {
            updateStatus('OMW')
        }
        toast({
            title: 'SMS Failed',
            text: 'Status updated but message not sent.',
            icon: 'alert-circle',
            position: 'bottom-center',
            iconClasses: 'text-yellow-500',
        })
    },
})

function sendSms() {
    smsLoading.value = true
    smsResource.fetch({
        stop_name: stop_name,
        contact_name: stop.value.contact,
        template_type: pendingSmsType.value,
        message: smsMessage.value,
    })
}

const updateStatusResource = createResource({
    url: 'projectit.api.update_stop_status',
    makeParams(args) {
        return {
            trip_name: trip_name,
            stop_name: stop_name,
            status: args.status,
        }
    },
    onSuccess(data) {
        stop.value.custom_status = data.updated_status
        actionLoading.value = false
        toast({
            title: 'Updated',
            text: `Status: ${data.updated_status}`,
            icon: 'check-circle',
            position: 'bottom-center',
            iconClasses: 'text-blue-500',
        })
    },
    onError(e) {
        errorMessage.value = e
        showError.value = true
        actionLoading.value = false
    },
})

function updateStatus(status) {
    updateStatusResource.fetch({ status })
}

// Check In
const checkinResource = createResource({
    url: 'projectit.api.route_checkin',
    onSuccess() {
        stop.value.custom_status = 'In Progress'
        stop.value.custom_checkin_time = new Date().toISOString()
        uploading.value = false
        toast({
            title: 'Checked In',
            text: 'Job started. Timer running.',
            icon: 'check-circle',
            position: 'bottom-center',
            iconClasses: 'text-blue-500',
        })
    },
    onError(e) {
        errorMessage.value = e
        showError.value = true
        uploading.value = false
    },
})

// Check Out
const checkoutResource = createResource({
    url: 'projectit.api.route_checkout',
    onSuccess() {
        stop.value.custom_status = 'Complete'
        stop.value.custom_checkout_time = new Date().toISOString()
        uploading.value = false
        toast({
            title: 'Checked Out',
            text: 'Job complete.',
            icon: 'check-circle',
            position: 'bottom-center',
            iconClasses: 'text-blue-500',
        })
        // Prompt completion SMS after checkout
        if (stop.value.phone) {
            openSmsPrompt('complete')
        }
    },
    onError(e) {
        errorMessage.value = e
        showError.value = true
        uploading.value = false
    },
})

async function handleImageCapture(file) {
    uploading.value = true
    showCamera.value = false

    const fileAttachment = new FileAttachment(file)
    const docName = stop.value.delivery_note || trip_name
    const docType = stop.value.delivery_note ? 'Delivery Note' : 'Delivery Trip'
    await fileAttachment.upload(docType, docName, '')

    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude
                const lng = position.coords.longitude
                if (cameraMode.value === 'Check-In') {
                    checkinResource.fetch({
                        employee_id: employee.name,
                        trip_name,
                        stop_name,
                        latitude: lat,
                        longitude: lng,
                    })
                } else {
                    checkoutResource.fetch({
                        employee_id: employee.name,
                        trip_name,
                        stop_name,
                        latitude: lat,
                        longitude: lng,
                    })
                }
            },
            (error) => {
                errorMessage.value = error.message
                showError.value = true
                uploading.value = false
            }
        )
    } else {
        errorMessage.value = 'Geolocation not supported by your device'
        showError.value = true
        uploading.value = false
    }
}
</script>
