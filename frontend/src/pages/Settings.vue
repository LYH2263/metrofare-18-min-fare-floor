<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const floor = ref('')
const saved = ref(false)
const error = ref('')

onMounted(async () => {
  const s = await getJSON('/api/settings')
  floor.value = s.floor_fare ?? ''
})

const save = async () => {
  saved.value = false
  error.value = ''
  const value = Number(floor.value)
  if (!Number.isFinite(value) || value <= 0) {
    error.value = '底价必须为正数'
    return
  }
  try {
    await putJSON('/api/settings', { floor_fare: value })
    saved.value = true
  } catch (e) {
    error.value = e.message
  }
}
</script>
<template>
  <div class="page"><h1>设置</h1>
    <div class="panel">
      <label>全程最低票价（底价，正数）</label>
      <p><input v-model="floor" type="number" min="0.01" step="0.5" /> 元</p>
      <p>分段价低于底价时，应付抬到底价并标记抬升；否则应付等于分段价。</p>
      <button @click="save">保存底价</button>
      <span v-if="saved" class="muted"> 已保存</span>
      <span v-if="error" class="err"> {{ error }}</span>
    </div>
  </div>
</template>
