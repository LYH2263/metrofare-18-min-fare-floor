<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
const run = async () => { out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: true }) }
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
      <template v-if="out.reachable">
        <p>站数 {{ out.hops }}</p>
        <div class="fare-duo">
          <div class="fare-cell"><div class="muted">分段价</div><div class="hero-num">¥{{ out.fare }}</div></div>
          <div class="fare-cell"><div class="muted">应付</div><div class="hero-num">¥{{ out.payable }}</div></div>
        </div>
        <p v-if="out.lifted" class="lifted">已按底价抬升</p>
        <p v-else class="muted">未抬升</p>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
