<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const s = ref({})
const minFare = ref('')
const msg = ref('')
const err = ref('')
const load = async () => {
  s.value = await getJSON('/api/settings')
  minFare.value = s.value.min_fare ?? ''
}
const save = async () => {
  msg.value = ''; err.value = ''
  try {
    s.value = await putJSON('/api/settings', { min_fare: Number(minFare.value) })
    minFare.value = s.value.min_fare
    msg.value = `底价已更新为 ¥${s.value.min_fare}`
  } catch (e) {
    err.value = '保存失败：底价必须是正数'
  }
}
onMounted(load)
</script>
<template>
  <div class="page"><h1>设置</h1>
    <div class="panel">
      <label>全程最低票价（底价）¥</label>
      <input v-model="minFare" type="number" min="0" step="0.5" />
      <button @click="save">保存</button>
      <p v-if="msg" class="muted">{{ msg }}</p>
      <p v-if="err" class="err">{{ err }}</p>
      <p class="muted">分段价低于底价时，应付抬升为底价；比价不读取一日通开关。</p>
    </div>
    <div class="panel"><pre>{{ s }}</pre></div>
  </div>
</template>
