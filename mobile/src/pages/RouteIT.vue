<template>
    <div>
        <div class="pt-4 pl-[21px]">
            <Tab :tabs="tabs" @selected-tab="selectedTab = $event"></Tab>
        </div>
        <div v-if="selectedTab === 'Route'">
            <RouteList></RouteList>
        </div>
        <div v-else-if="selectedTab === 'Clock'">
            <ClockTab></ClockTab>
        </div>
        <div v-else>
            <WorkITEntries></WorkITEntries>
        </div>
    </div>
</template>
<script setup>
import { ref } from 'vue'
import Tab from '../components/Tab.vue'
import RouteList from './RouteList.vue'
import ClockTab from './ClockTab.vue'
import WorkITEntries from './WorkITEntries.vue'
import { moduleName } from '../data/module'

const tabs = ['Route', 'Clock', 'Entries']
const selectedTab = ref('Route')
moduleName.value = 'RouteIT'
</script>
