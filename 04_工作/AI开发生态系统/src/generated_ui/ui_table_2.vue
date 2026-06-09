<template>
  <div class="container mt-5">
    <div class="card">
      <div class="card-body text-center py-5">
        <h3>UI 组件</h3>
        <p class="text-muted">Vue 组件示例</p>
        <button class="btn btn-primary me-2" @click="confirm">确定</button>
        <button class="btn btn-secondary" @click="cancel">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const confirm = () => console.log("confirmed");
const cancel = () => console.log("cancelled");
</script>