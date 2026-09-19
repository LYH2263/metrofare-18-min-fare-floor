<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
// 只读试算：不落库
const run = async () => { out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: false }) }
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <button @click="run">试算</button>
    </div>
    <div v-if="out" class="panel">
      <p v-if="out.reachable">
        站数 {{ out.hops }}
        <span :class="['badge', out.lifted ? 'badge-lift' : 'badge-flat']">{{ out.lifted ? '已抬升' : '未抬升' }}</span>
      </p>
      <div v-if="out.reachable" class="fare-cells">
        <div class="fare-cell"><div class="muted">分段价</div><div class="v">¥{{ out.fare }}</div></div>
        <div class="fare-cell"><div class="muted">应付</div><div class="v">¥{{ out.payable }}</div></div>
      </div>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
