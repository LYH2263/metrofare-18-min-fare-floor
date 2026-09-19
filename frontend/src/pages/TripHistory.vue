<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const detail = ref(null)
const error = ref('')

onMounted(async () => { items.value = (await getJSON('/api/history')).items })

const open = async (id) => {
  detail.value = null
  error.value = ''
  try {
    const row = await getJSON(`/api/history/${id}`)
    detail.value = row
  } catch (e) {
    error.value = e.message
  }
}
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table><tr v-for="h in items" :key="h.id">
      <td class="clickable" @click="open(h.id)">#{{ h.id }}</td>
      <td>{{ h.created_at }}</td>
    </tr></table>

    <div v-if="detail" class="panel">
      <h2>记录 #{{ detail.id }}（写入当时快照）</h2>
      <template v-if="detail.result && detail.result.reachable">
        <p>{{ detail.result.start }} → {{ detail.result.end }} · 站数 {{ detail.result.hops }}</p>
        <div class="fare-cells">
          <div class="fare-cell"><div class="muted">分段价</div><div class="v">¥{{ detail.result.fare }}</div></div>
          <div class="fare-cell">
            <div class="muted">应付</div><div class="v">¥{{ detail.result.payable }}</div>
          </div>
        </div>
        <p><span :class="['badge', detail.result.lifted ? 'badge-lift' : 'badge-flat']">
          {{ detail.result.lifted ? '已抬升' : '未抬升' }}
        </span></p>
      </template>
      <p v-else-if="detail.result" class="muted">{{ detail.result.start }} → {{ detail.result.end }}：不可达</p>
      <p v-else class="muted">该记录写入时未包含底价字段。</p>
    </div>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>
