<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const runId = ref('')
const detail = ref(null)
const err = ref('')
const open = async (id) => {
  const rid = id ?? runId.value
  if (!rid) return
  err.value = ''; detail.value = null
  try {
    detail.value = await getJSON(`/api/history/${rid}`)
    runId.value = String(rid)
  } catch (e) {
    err.value = `编号 ${rid} 的记录不存在`
  }
}
onMounted(async () => { items.value = (await getJSON('/api/history')).items })
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <div class="panel">
      <input v-model="runId" type="number" min="1" placeholder="记录编号" />
      <button @click="open()">按编号打开</button>
      <p v-if="err" class="err">{{ err }}</p>
    </div>
    <div v-if="detail" class="panel">
      <p>#{{ detail.id }} · {{ detail.created_at }} · {{ detail.input.start }} → {{ detail.input.end }}</p>
      <template v-if="detail.result.reachable">
        <p>站数 {{ detail.result.hops }}</p>
        <div class="fare-duo">
          <div class="fare-cell"><div class="muted">分段价</div><div class="hero-num">¥{{ detail.result.fare }}</div></div>
          <div class="fare-cell"><div class="muted">应付</div><div class="hero-num">¥{{ detail.result.payable }}</div></div>
        </div>
        <p v-if="detail.result.lifted" class="lifted">已按底价抬升</p>
        <p v-else class="muted">未抬升</p>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
    <table>
      <tr v-for="h in items" :key="h.id" class="row-link" @click="open(h.id)">
        <td>#{{ h.id }}</td><td>{{ h.created_at }}</td>
      </tr>
    </table>
  </div>
</template>
